"""
Knowledge feature — ingestion service.

Handles all CPU-bound document processing: text extraction, chunking,
local embedding generation, and ChromaDB storage. Because these operations
are I/O- and CPU-heavy, the main entry point (`process_knowledge_source`)
offloads the work to a thread-pool executor so the AsyncIO event loop is
never blocked.

Supported file formats: PDF (.pdf), plain text (.txt), Markdown (.md), CSV (.csv).
"""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from gm_shield.shared.database.chroma import get_chroma_client
from gm_shield.core.logging import get_logger
from gm_shield.shared.database.sqlite import SessionLocal
from gm_shield.features.knowledge.models import KnowledgeSource

logger = get_logger(__name__)

# ── Embedding model ──────────────────────────────────────────────────────────
# Using a lightweight local model that runs entirely offline.
# Loaded once and reused across all ingestion jobs (lazy singleton pattern).
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """
    Return the shared sentence-transformer embedding model, loading it on first call.

    The model is loaded once and cached in the module-level ``_embedding_model``
    variable to avoid reloading on every request.

    Returns:
        A ``SentenceTransformer`` instance for ``all-MiniLM-L6-v2``.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info("embedding_model_loading", model=EMBEDDING_MODEL_NAME)
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


# ── Text extraction ──────────────────────────────────────────────────────────


def extract_text_from_file(file_path: str) -> str:
    """
    Extract raw text from a file, dispatching to the appropriate parser by extension.

    Args:
        file_path: Absolute or relative path to the source file.
            Supported extensions: ``.pdf``, ``.txt``, ``.md``, ``.csv``.

    Returns:
        The full extracted text as a single string.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist on disk.
        ValueError: If the file extension is not supported.

    Supported formats:
        - ``.pdf`` — extracted page-by-page using PyPDF
        - ``.txt`` / ``.md`` — read as UTF-8 plain text
        - ``.csv`` — loaded with pandas and serialised to string
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()

    try:
        if ext == ".pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text

        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif ext == ".csv":
            df = pd.read_csv(file_path)
            return df.to_string()

        else:
            raise ValueError(f"Unsupported file type: {ext}")

    except Exception as e:
        logger.error("text_extraction_failed", file_path=file_path, error=str(e))
        raise


# ── Core processing pipeline ─────────────────────────────────────────────────


def _update_task_state(
    session: Session,
    source_id: int,
    status: str = None,
    progress: float = None,
    step: str = None,
    error: str = None,
    started_at: datetime = None,
):
    """Helper to update the KnowledgeSource record in a thread-safe way."""
    try:
        # Re-query inside the session to attach the object
        source = (
            session.query(KnowledgeSource)
            .filter(KnowledgeSource.id == source_id)
            .first()
        )
        if not source:
            return

        if status:
            source.status = status
        if progress is not None:
            source.progress = progress
        if step:
            source.current_step = step
        if error:
            source.error_message = error
        if started_at:
            source.started_at = started_at

        session.commit()
    except Exception as e:
        logger.error(f"Failed to update task state for source {source_id}: {e}")
        session.rollback()


def _process_sync(source_id: int) -> str:
    """
    Run the full ingestion pipeline for a single source (blocking).
    Updates status in SQLite database throughout the process.

    Args:
        source_id: ID of the KnowledgeSource record to process.

    Returns:
        A summary string.
    """
    session = SessionLocal()
    source_record = (
        session.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
    )

    if not source_record:
        logger.error("knowledge_source_not_found", source_id=source_id)
        return "Source not found"

    file_path = source_record.file_path
    logger.info("ingestion_started", file_path=file_path, source_id=source_id)

    try:
        # 1. Start
        _update_task_state(
            session,
            source_id,
            status="running",
            progress=0.0,
            step="Extracting text",
            started_at=datetime.now(timezone.utc),
        )

        # 2. Extract
        text = extract_text_from_file(file_path)
        if not text.strip():
            logger.warning("no_text_extracted", file_path=file_path)
            _update_task_state(
                session, source_id, status="failed", error="No text content found"
            )
            return "No text content found"

        # 3. Chunk
        _update_task_state(session, source_id, progress=20.0, step="Chunking text")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        logger.info("chunks_generated", file_path=file_path, chunk_count=len(chunks))

        if not chunks:
            _update_task_state(
                session, source_id, status="failed", error="No chunks generated"
            )
            return "No chunks generated"

        # 4. Embed (Batched)
        _update_task_state(
            session, source_id, progress=30.0, step="Generating embeddings"
        )
        model = get_embedding_model()

        batch_size = 32
        total_chunks = len(chunks)
        embeddings = []

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]
            batch_embeddings = model.encode(batch)
            embeddings.extend(batch_embeddings)

            # Calculate progress between 30% and 90%
            current_progress = 30.0 + (
                60.0 * (min(i + batch_size, total_chunks) / total_chunks)
            )
            _update_task_state(
                session,
                source_id,
                progress=current_progress,
                step=f"Generating embeddings ({min(i + batch_size, total_chunks)}/{total_chunks})",
            )

        # 5. Store in ChromaDB
        _update_task_state(
            session, source_id, progress=90.0, step="Storing in Vector DB"
        )
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="knowledge_base")

        # Collect existing vector IDs before write. We only delete them after the
        # replacement write succeeds to avoid data loss on transient write errors.
        existing_chunks = collection.get(where={"source": file_path}, include=[])
        existing_ids = existing_chunks.get("ids", [])

        base_id = uuid.uuid4().hex[:8]
        ids = [f"{Path(file_path).name}_{base_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {"source": file_path, "chunk_index": i} for i in range(len(chunks))
        ]

        collection.add(
            documents=chunks,
            embeddings=[e.tolist() for e in embeddings],  # numpy array to list
            metadatas=metadatas,
            ids=ids,
        )

        # Delete old chunks for this file only after the replacement set is
        # successfully written.
        if existing_ids:
            collection.delete(ids=existing_ids)

        # 6. Complete
        source_record = (
            session.query(KnowledgeSource)
            .filter(KnowledgeSource.id == source_id)
            .first()
        )
        if source_record:
            source_record.status = "completed"
            source_record.progress = 100.0
            source_record.current_step = "Done"
            source_record.last_indexed_at = datetime.now(timezone.utc)
            source_record.chunk_count = len(chunks)
            source_record.error_message = None
            if not source_record.features:
                source_record.features = ["indexation"]  # Default feature
            session.commit()

        logger.info("ingestion_complete", file_path=file_path, chunk_count=len(chunks))
        return f"Processed {len(chunks)} chunks"

    except Exception as e:
        logger.error("ingestion_failed", source_id=source_id, error=str(e))
        _update_task_state(session, source_id, status="failed", error=str(e))
        return f"Failed: {e}"
    finally:
        session.close()


# ── Async entry point ─────────────────────────────────────────────────────────


async def process_knowledge_source(source_id: int) -> str:
    """
    Async entry-point for the knowledge-source ingestion pipeline.

    Args:
        source_id: ID of the KnowledgeSource record.

    Returns:
        The summary string returned by :func:`_process_sync`.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _process_sync, source_id)


# ── List & stats ──────────────────────────────────────────────────────────────


def _get_knowledge_list_sync() -> list[dict]:
    """Sync implementation of get_knowledge_list."""
    db = SessionLocal()
    try:
        sources = (
            db.query(KnowledgeSource).order_by(KnowledgeSource.created_at.desc()).all()
        )
        # Convert to dicts matching the schema
        results = []
        for s in sources:
            results.append(
                {
                    "id": s.id,
                    "source": s.source,
                    "filename": s.filename,
                    "chunk_count": s.chunk_count,
                    "status": s.status,
                    "progress": s.progress,
                    "current_step": s.current_step,
                    "started_at": s.started_at,
                    "last_indexed_at": s.last_indexed_at,
                    "error_message": s.error_message,
                    "features": s.features or [],
                }
            )
        return results
    finally:
        db.close()


async def get_knowledge_list() -> list[dict]:
    """
    Returns a list of all knowledge sources with their status from SQLite.
    """
    return await asyncio.to_thread(_get_knowledge_list_sync)


def _get_knowledge_stats_sync() -> dict:
    """Sync implementation of get_knowledge_stats."""
    db = SessionLocal()
    try:
        doc_count = db.query(KnowledgeSource).count()
        chunk_count = (
            db.query(KnowledgeSource).with_entities(KnowledgeSource.chunk_count).all()
        )
        total_chunks = sum(c[0] for c in chunk_count)
        return {
            "document_count": doc_count,
            "chunk_count": total_chunks,
        }
    finally:
        db.close()


async def get_knowledge_stats() -> dict:
    """
    Async wrapper — returns aggregate stats for the knowledge base.

    Returns a dict with: ``document_count``, ``chunk_count``.
    """
    return await asyncio.to_thread(_get_knowledge_stats_sync)


def create_or_update_knowledge_source(file_path: str) -> int:
    """
    Create a new knowledge source record or reset an existing one.
    Returns the source ID.
    """
    db = SessionLocal()
    try:
        existing = (
            db.query(KnowledgeSource)
            .filter(KnowledgeSource.file_path == file_path)
            .first()
        )

        if existing:
            new_source = existing
            new_source.status = "pending"
            new_source.progress = 0.0
            new_source.current_step = "Queued"
            new_source.error_message = None
            # Preserve created_at, update updated_at automatically
        else:
            new_source = KnowledgeSource(
                file_path=file_path, status="pending", current_step="Queued"
            )
            db.add(new_source)

        db.commit()
        db.refresh(new_source)
        return new_source.id
    finally:
        db.close()


def refresh_knowledge_source(source_id: int) -> None:
    """
    Reset a source to pending state to be picked up by the queue.
    NOTE: The caller (router) is responsible for enqueuing the task.
    This function just resets the state in DB.
    """
    db = SessionLocal()
    try:
        source = (
            db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
        )
        if not source:
            raise ValueError(f"Source {source_id} not found")

        source.status = "pending"
        source.progress = 0.0
        source.current_step = "Queued for refresh"
        source.error_message = None
        source.started_at = None
        db.commit()
    finally:
        db.close()

    # We do NOT return the list here anymore to avoid async issues in synchronous context
    # The router handles the response which doesn't require this return value
    return None


# ── Semantic Search ───────────────────────────────────────────────────────────


def _query_knowledge_sync(query: str, top_k: int = 5) -> list[dict]:
    """
    Search ChromaDB for chunks semantically similar to the target query (blocking).

    Returns a list of dicts, each containing:
    - ``content``: The text content of the chunk.
    - ``metadata``: Source metadata (e.g. file path).
    - ``score``: Similarity distance (lower is better for L2).
    """
    logger.info("knowledge_query_started", query=query, top_k=top_k)

    # 1. Embed the query
    model = get_embedding_model()
    query_embedding = model.encode([query])

    # 2. Query ChromaDB
    client = get_chroma_client()
    try:
        collection = client.get_collection(name="knowledge_base")
    except ValueError:
        return []

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # 3. Format results
    formatted = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i in range(len(documents)):
        formatted.append(
            {
                "content": documents[i],
                "metadata": metadatas[i],
                "score": distances[i],
            }
        )

    return formatted


async def query_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """
    Async wrapper for semantic search in the knowledge base.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _query_knowledge_sync, query, top_k)
