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
import logging
import uuid
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from gm_shield.shared.database.chroma import get_chroma_client

logger = logging.getLogger(__name__)

# ── Embedding model ──────────────────────────────────────────────────────────
# Using a lightweight local model that runs entirely offline.
# Loaded once and reused across all ingestion jobs (lazy singleton pattern).
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_embedding_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Return the shared sentence-transformer embedding model, loading it on first call.

    Uses a module-level singleton so the model weights are loaded from disk only once
    per process, regardless of how many ingestion tasks run concurrently.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL_NAME)
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


# ── Text extraction ──────────────────────────────────────────────────────────


def extract_text_from_file(file_path: str) -> str:
    """
    Extract raw text from a file, dispatching to the appropriate parser by extension.

    Args:
        file_path: Absolute or relative path to the source file.

    Returns:
        The full extracted text as a single string.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
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
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)

        if ext in {".txt", ".md"}:
            return path.read_text(encoding="utf-8")

        if ext == ".csv":
            df = pd.read_csv(file_path)
            return df.to_string()

        raise ValueError(f"Unsupported file type: {ext!r}")

    except (FileNotFoundError, ValueError):
        raise
    except Exception as e:
        logger.error("Error extracting text from %s: %s", file_path, e)
        raise


# ── Core processing pipeline ─────────────────────────────────────────────────


def _process_sync(file_path: str) -> str:
    """
    Synchronous document processing pipeline — intended to run inside a thread-pool.

    Pipeline steps:
        1. **Extract** raw text from the file.
        2. **Chunk** text into overlapping segments (1 000 tokens / 200 overlap).
        3. **Embed** each chunk using the local sentence-transformer model.
        4. **Store** embeddings + metadata in ChromaDB under the ``knowledge_base`` collection.

    Args:
        file_path: Path to the source document (must already exist on disk).

    Returns:
        A human-readable summary string, e.g. ``"Processed 42 chunks"``.
    """
    logger.info("Starting ingestion pipeline for: %s", file_path)

    # Step 1 — Extract
    text = extract_text_from_file(file_path)
    if not text.strip():
        logger.warning("No text extracted from: %s", file_path)
        return "No text content found"

    # Step 2 — Chunk
    # RecursiveCharacterTextSplitter tries to keep paragraphs/sentences intact.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    logger.info("Generated %d chunks from: %s", len(chunks), file_path)

    if not chunks:
        return "No chunks generated"

    # Step 3 — Embed
    model = get_embedding_model()
    embeddings = model.encode(chunks)

    # Step 4 — Store in ChromaDB
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="knowledge_base")

    # Prefix chunk IDs with a short random hex so the same file can be re-ingested
    # without colliding with previous runs.
    base_id = uuid.uuid4().hex[:8]
    source_name = Path(file_path).name
    ids = [f"{source_name}_{base_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids,
    )

    logger.info("Stored %d chunks in ChromaDB for: %s", len(chunks), file_path)
    return f"Processed {len(chunks)} chunks"


# ── Async entry point ─────────────────────────────────────────────────────────


async def process_knowledge_source(file_path: str) -> str:
    """
    Async wrapper for the document ingestion pipeline.

    Delegates CPU-bound work to the default thread-pool executor via
    ``asyncio.get_running_loop().run_in_executor``, keeping the event loop free
    to handle other requests during processing.

    Args:
        file_path: Path to the source document to ingest.

    Returns:
        Processing summary string from ``_process_sync``.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _process_sync, file_path)
