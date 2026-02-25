import chromadb
from gm_shield.core.config import settings


def get_chroma_client():
    """
    Returns a ChromaDB client.
    """
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
