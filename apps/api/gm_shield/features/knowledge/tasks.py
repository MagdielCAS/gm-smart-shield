"""
Async task registration for Knowledge feature.
This file handles background processing of uploaded documents (extraction, indexing, etc.).
"""

from gm_shield.core.logging import get_logger
from gm_shield.features.knowledge.service import process_knowledge_source
from gm_shield.features.knowledge.models import CharacterSheetTemplate, QuickReference
from gm_shield.shared.database.sqlite import SessionLocal
from gm_shield.features.knowledge.agents.sheet import SheetAgent
from gm_shield.features.knowledge.agents.reference import ReferenceAgent

logger = get_logger(__name__)


async def run_knowledge_ingestion(source_id: int):
    """
    Task entry point for knowledge ingestion pipeline.
    This typically runs:
    1. Text extraction & Chunking (via process_knowledge_source)
    2. Vector embedding & storage (via process_knowledge_source)
    3. Sheet Agent extraction
    4. Reference Agent extraction
    """
    logger.info("knowledge_task_started", source_id=source_id)

    # 1. Standard ingestion (Text -> Chunks -> VectorDB)
    # This function manages its own database state updates.
    result = await process_knowledge_source(source_id)
    logger.info("knowledge_ingestion_finished", source_id=source_id, result=result)

    # Run specialized agents (fire and forget sequentially for now, or parallel if we had more resources)
    try:
        await run_sheet_extraction(source_id)
    except Exception as e:
        logger.error("sheet_extraction_task_failed", source_id=source_id, error=str(e))

    try:
        await run_reference_extraction(source_id)
    except Exception as e:
        logger.error(
            "reference_extraction_task_failed", source_id=source_id, error=str(e)
        )


async def run_sheet_extraction(source_id: int):
    """
    Runs the Sheet Agent to extract character sheet templates from the ingested document.
    """
    from gm_shield.features.knowledge.models import KnowledgeSource

    logger.info("sheet_extraction_started", source_id=source_id)

    session = SessionLocal()
    try:
        source = (
            session.query(KnowledgeSource)
            .filter(KnowledgeSource.id == source_id)
            .first()
        )
        if not source or source.status != "completed":
            logger.warning(
                "sheet_extraction_skipped_invalid_source",
                source_id=source_id,
                status=getattr(source, "status", "unknown"),
            )
            return

        # Use RAG to find relevant pages instead of reading the whole text
        from gm_shield.shared.database.chroma import get_chroma_client
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="knowledge_base")
        
        try:
            results = collection.query(
                query_texts=["character sheet template, attributes, skills, equipment, class details"],
                n_results=10,
                where={"source": source.file_path}
            )
            
            if not results or not results["documents"] or not results["documents"][0]:
                logger.warning("sheet_extraction_no_relevant_pages_found", source_id=source_id)
                return
                
            # Combine the text of the top matching pages to provide context to the SheetAgent
            relevant_pages = results["documents"][0]
            text = "\n\n...[Page Break]...\n\n".join(relevant_pages)
            
        except Exception as e:
            logger.error("sheet_extraction_chroma_query_failed", error=str(e))
            return

        agent = SheetAgent()
        template_schema = await agent.extract_template(text)

        if template_schema:
            logger.info(
                "sheet_extraction_success", template_name=template_schema.template_name
            )

            # Save to DB
            template = CharacterSheetTemplate(
                source_id=source_id,
                name=template_schema.template_name,
                system=template_schema.system_name,
                template_schema=template_schema.sections,
            )
            session.add(template)

            # Update source to indicate this feature was processed
            features = list(source.features) if source.features else []
            if "character_sheet" not in features:
                features.append("character_sheet")
                source.features = features

            session.commit()
        else:
            logger.info("sheet_extraction_no_template_found")

    except Exception as e:
        logger.error("sheet_extraction_failed", error=str(e))
        session.rollback()
    finally:
        session.close()


async def run_reference_extraction(source_id: int):
    """
    Runs the Reference Agent to extract spells, items, etc.
    This is computationally expensive, so we might only do it for shorter docs or chunks in a real prod env.
    For this implementation, we will sample the first 15000 characters or key sections.
    """
    from gm_shield.features.knowledge.models import KnowledgeSource

    logger.info("reference_extraction_started", source_id=source_id)

    session = SessionLocal()
    try:
        source = (
            session.query(KnowledgeSource)
            .filter(KnowledgeSource.id == source_id)
            .first()
        )
        if not source or source.status != "completed":
            return

        # Use RAG to find relevant pages instead of reading the whole text
        from gm_shield.shared.database.chroma import get_chroma_client
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="knowledge_base")
        
        try:
            results = collection.query(
                query_texts=["spells, weapons, equipment, items, feats, traits list"],
                n_results=10,
                where={"source": source.file_path}
            )
            
            if not results or not results["documents"] or not results["documents"][0]:
                logger.warning("reference_extraction_no_relevant_pages_found", source_id=source_id)
                return
                
            # Combine the text of the top matching pages to provide context to the ReferenceAgent
            relevant_pages = results["documents"][0]
            text_chunk = "\n\n...[Page Break]...\n\n".join(relevant_pages)
            
        except Exception as e:
            logger.error("reference_extraction_chroma_query_failed", error=str(e))
            return

        agent = ReferenceAgent()
        result = await agent.extract_references(text_chunk)

        items = result.items if result else []

        if items:
            logger.info("reference_extraction_success", count=len(items))
            for item in items:
                ref = QuickReference(
                    source_id=source_id,
                    name=item.name,
                    category=item.category,
                    description=item.description,
                    tags=item.tags,
                    source_page=item.source_page,
                    source_section=item.source_section,
                )
                session.add(ref)

            # Update features metadata
            features = list(source.features) if source.features else []
            if "quick_reference" not in features:
                features.append("quick_reference")
                source.features = features

            session.commit()
        else:
            logger.info("reference_extraction_no_items_found")

    except Exception as e:
        logger.error("reference_extraction_failed", error=str(e))
        session.rollback()
    finally:
        session.close()
