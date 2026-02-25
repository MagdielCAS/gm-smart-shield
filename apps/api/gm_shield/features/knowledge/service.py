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

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model

def extract_text_from_file(file_path: str) -> str:
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
        logger.error(f"Error extracting text from {file_path}: {e}")
        raise

def _process_sync(file_path: str):
    """
    Synchronous processing logic to run in a thread pool.
    """
    logger.info(f"Starting processing for {file_path}")

    # 1. Extract
    text = extract_text_from_file(file_path)
    if not text.strip():
        logger.warning(f"No text extracted from {file_path}")
        return "No text content found"

    # 2. Chunk
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    logger.info(f"Generated {len(chunks)} chunks from {file_path}")

    if not chunks:
        return "No chunks generated"

    # 3. Embed
    model = get_embedding_model()
    embeddings = model.encode(chunks)

    # 4. Store
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="knowledge_base")

    # Generate unique IDs for chunks to avoid collisions if re-processing same file?
    # Or use stable IDs based on content hash?
    # For now, simple file-based IDs are okay, maybe append timestamp or uuid
    base_id = uuid.uuid4().hex[:8]
    ids = [f"{Path(file_path).name}_{base_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids
    )

    logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB")
    return f"Processed {len(chunks)} chunks"

async def process_knowledge_source(file_path: str):
    """
    Async wrapper to run processing in a thread pool.
    """
    loop = asyncio.get_running_loop()
    # Run the CPU-bound task in a default executor (thread pool)
    return await loop.run_in_executor(None, _process_sync, file_path)
