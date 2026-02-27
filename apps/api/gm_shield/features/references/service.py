"""
Reference Service — orchestrates quick reference generation.

Retrieves rulebook content for specific categories (e.g. spells, races)
and invokes the Reference Agent.
"""

from typing import Dict, Any, List
from gm_shield.features.knowledge.service import query_knowledge
from gm_shield.features.references.agent import ReferenceAgent
from gm_shield.features.references.models import ReferenceResponse
from gm_shield.shared.ai.base import Citation
from gm_shield.core.logging import get_logger

logger = get_logger(__name__)


class ReferenceService:
    """
    Service for generating category-specific quick references.
    """

    def __init__(self):
        self.agent = ReferenceAgent()

    async def generate_reference(self, category: str, source_id: str) -> ReferenceResponse:
        """
        Retrieves context for a category and generates a summary.
        """
        logger.info("reference_service_generate", category=category, source_id=source_id)

        # 1. Retrieve context based on category
        query = f"{category} rules descriptions list"
        chunks = await query_knowledge(query, top_k=5)

        context_parts = []
        citations = []

        for chunk in chunks:
            content = chunk["content"]
            metadata = chunk["metadata"]
            source = metadata.get("source", "unknown")

            # Filter by source_id if provided
            if source_id in source:
                context_parts.append(f"Source: {source}\nContent: {content}")
                citations.append(
                    Citation(source=source, content=content, page=metadata.get("page"))
                )

        if not context_parts:
             # Fallback if specific source not matched
             for chunk in chunks:
                content = chunk["content"]
                metadata = chunk["metadata"]
                source = metadata.get("source", "unknown")
                context_parts.append(f"Source: {source}\nContent: {content}")
                citations.append(
                    Citation(source=source, content=content, page=metadata.get("page"))
                )

        context = "\n\n---\n\n".join(context_parts)

        # 2. Generate Content
        response = await self.agent.process(
            query="generate_reference",
            context=context,
            citations=citations,
            category=category
        )

        return ReferenceResponse(
            category=category,
            content=response.text,
            metadata=response.metadata
        )

# Singleton
_reference_service = ReferenceService()

def get_reference_service() -> ReferenceService:
    return _reference_service
