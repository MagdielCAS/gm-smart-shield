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
    Create and return a ChromaDB persistent client.

    A new client instance is created on every call. The underlying data is
    stored at the path configured in ``settings.CHROMA_PERSIST_DIRECTORY``,
    so state is shared across calls through the filesystem.

    Returns:
        chromadb.PersistentClient: A client connected to the local ChromaDB store.
    """
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
