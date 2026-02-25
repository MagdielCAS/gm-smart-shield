"""
ChromaDB client adapter — shared infrastructure.

Provides a thin factory function that constructs a configured ChromaDB
``PersistentClient`` pointing at the local data directory.

All feature slices that need to interact with the vector store should use
``get_chroma_client()`` rather than constructing the client directly, so that
the persistence path is always sourced from the central ``Settings`` object.
"""

import chromadb
from gm_shield.core.config import settings


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Create and return a ChromaDB ``PersistentClient``.

    Each call creates a new client instance pointed at
    ``settings.CHROMA_PERSIST_DIRECTORY``. ChromaDB's ``PersistentClient``
    is lightweight to construct — it does **not** load all collections into
    memory on initialisation.

    Returns:
        chromadb.PersistentClient: A client connected to the local ChromaDB store.
    """
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
