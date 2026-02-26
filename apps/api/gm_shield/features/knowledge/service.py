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
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from gm_shield.shared.database.chroma import get_chroma_client
from gm_shield.core.logging import get_logger

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


def _process_sync(file_path: str) -> str:
    """
    Run the full ingestion pipeline for a single file (blocking).

    Intended to be called inside a thread-pool executor via
    :func:`process_knowledge_source` so the event loop is not blocked.

    Pipeline steps:
        1. Extract raw text from the file.
        2. Split the text into overlapping chunks using a recursive character splitter.
        3. Embed the chunks with the local ``all-MiniLM-L6-v2`` sentence-transformer.
        4. Upsert the embedded chunks into the ChromaDB ``knowledge_base`` collection.

    Args:
        file_path: Path to the file to ingest.

    Returns:
        A summary string, e.g. ``"Processed 42 chunks"``.
    """
    logger.info("ingestion_started", file_path=file_path)

    # Step 1 — Extract
    text = extract_text_from_file(file_path)
    if not text.strip():
        logger.warning("no_text_extracted", file_path=file_path)
        return "No text content found"

    # Step 2 — Chunk
    # RecursiveCharacterTextSplitter tries to keep paragraphs/sentences intact.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    logger.info("chunks_generated", file_path=file_path, chunk_count=len(chunks))

    if not chunks:
        return "No chunks generated"

    # Step 3 — Embed
    model = get_embedding_model()
    embeddings = model.encode(chunks)

    # Step 4 — Store in ChromaDB
    # IDs are randomised per ingestion run to allow re-processing the same file
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="knowledge_base")

    base_id = uuid.uuid4().hex[:8]
    ids = [f"{Path(file_path).name}_{base_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids,
    )

    logger.info("ingestion_complete", file_path=file_path, chunk_count=len(chunks))
    return f"Processed {len(chunks)} chunks"


# ── Async entry point ─────────────────────────────────────────────────────────


async def process_knowledge_source(file_path: str) -> str:
    """
    Async entry-point for the knowledge-source ingestion pipeline.

    Delegates CPU-bound work to a thread-pool executor so the asyncio event
    loop remains unblocked while text extraction, chunking, and embedding run.

    Args:
        file_path: Path to the file to ingest (passed through to :func:`_process_sync`).

    Returns:
        The summary string returned by :func:`_process_sync`.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _process_sync, file_path)


# ── List & stats ──────────────────────────────────────────────────────────────


def _list_sources_sync() -> list[dict]:
    """
    Query ChromaDB and aggregate chunk metadata by source file (blocking).

    Returns a list of dicts with keys: ``source``, ``filename``, ``chunk_count``.
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(name="knowledge_base")
    except ValueError as err:
        # Collection does not exist yet — no documents ingested.
        if "does not exist" not in str(err).lower():
            raise
        return []

    result = collection.get(include=["metadatas"])
    metadatas = result.get("metadatas") or []

    # Group by source file path
    sources: dict[str, int] = {}
    for meta in metadatas:
        src = meta.get("source", "unknown") if meta else "unknown"
        sources[src] = sources.get(src, 0) + 1

    return [
        {"source": src, "filename": src.split("/")[-1], "chunk_count": count}
        for src, count in sorted(sources.items())
    ]


async def get_knowledge_list() -> list[dict]:
    """
    Async wrapper — returns a list of unique knowledge sources from ChromaDB.

    Each item contains: ``source``, ``filename``, ``chunk_count``.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _list_sources_sync)


async def get_knowledge_stats() -> dict:
    """
    Async wrapper — returns aggregate stats for the knowledge base.

    Returns a dict with: ``document_count``, ``chunk_count``.
    """
    items = await get_knowledge_list()
    return {
        "document_count": len(items),
        "chunk_count": sum(i["chunk_count"] for i in items),
    }
