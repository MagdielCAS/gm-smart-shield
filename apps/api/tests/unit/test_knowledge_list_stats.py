"""
Unit tests for knowledge service list & stats functions.

Tests `get_knowledge_list` and `get_knowledge_stats` by mocking the ChromaDB
client, ensuring correct grouping, empty-collection handling, and aggregate
calculations without touching real storage.
"""

import pytest
from unittest.mock import MagicMock, patch
from gm_shield.features.knowledge.service import (
    get_knowledge_list,
    get_knowledge_stats,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_chroma_result(metadatas: list[dict | None]) -> dict:
    """Build a minimal ChromaDB `collection.get()` return value."""
    return {"metadatas": metadatas}


# ── get_knowledge_list ────────────────────────────────────────────────────────


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_list_returns_grouped_sources(mock_chroma):
    """Sources with multiple chunks are grouped into a single item."""
    collection = MagicMock()
    collection.get.return_value = _make_chroma_result(
        [
            {"source": "/docs/rulebook.pdf", "chunk_index": 0},
            {"source": "/docs/rulebook.pdf", "chunk_index": 1},
            {"source": "/docs/monsters.txt", "chunk_index": 0},
        ]
    )
    mock_chroma.return_value.get_collection.return_value = collection

    result = await get_knowledge_list()

    assert len(result) == 2
    rulebook = next(r for r in result if r["filename"] == "rulebook.pdf")
    assert rulebook["chunk_count"] == 2
    monsters = next(r for r in result if r["filename"] == "monsters.txt")
    assert monsters["chunk_count"] == 1


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_list_empty_when_no_collection(mock_chroma):
    """Returns an empty list when the ChromaDB collection does not exist yet."""
    mock_chroma.return_value.get_collection.side_effect = ValueError(
        "Collection knowledge_base does not exist"
    )

    result = await get_knowledge_list()

    assert result == []


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_list_empty_when_no_chunks(mock_chroma):
    """Returns an empty list when the collection exists but has no chunks."""
    collection = MagicMock()
    collection.get.return_value = _make_chroma_result([])
    mock_chroma.return_value.get_collection.return_value = collection

    result = await get_knowledge_list()

    assert result == []


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_list_handles_none_metadatas(mock_chroma):
    """Chunks with None metadata are grouped under 'unknown'."""
    collection = MagicMock()
    collection.get.return_value = _make_chroma_result([None, None])
    mock_chroma.return_value.get_collection.return_value = collection

    result = await get_knowledge_list()

    assert len(result) == 1
    assert result[0]["source"] == "unknown"
    assert result[0]["chunk_count"] == 2


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_list_item_shape(mock_chroma):
    """Each result item has source, filename, and chunk_count keys."""
    collection = MagicMock()
    collection.get.return_value = _make_chroma_result(
        [
            {"source": "/path/to/doc.pdf", "chunk_index": 0},
        ]
    )
    mock_chroma.return_value.get_collection.return_value = collection

    result = await get_knowledge_list()

    assert result[0]["source"] == "/path/to/doc.pdf"
    assert result[0]["filename"] == "doc.pdf"
    assert result[0]["chunk_count"] == 1


# ── get_knowledge_stats ───────────────────────────────────────────────────────


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_stats_aggregates_correctly(mock_chroma):
    """Stats correctly count distinct documents and total chunks."""
    collection = MagicMock()
    collection.get.return_value = _make_chroma_result(
        [
            {"source": "/a.pdf", "chunk_index": 0},
            {"source": "/a.pdf", "chunk_index": 1},
            {"source": "/b.txt", "chunk_index": 0},
        ]
    )
    mock_chroma.return_value.get_collection.return_value = collection

    stats = await get_knowledge_stats()

    assert stats["document_count"] == 2
    assert stats["chunk_count"] == 3


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_stats_zero_when_empty(mock_chroma):
    """Stats are zero when no documents have been ingested."""
    mock_chroma.return_value.get_collection.side_effect = ValueError(
        "Collection knowledge_base does not exist"
    )

    stats = await get_knowledge_stats()

    assert stats["document_count"] == 0
    assert stats["chunk_count"] == 0


@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_get_knowledge_list_raises_on_non_missing_collection_errors(mock_chroma):
    """Unexpected ChromaDB errors are raised instead of being masked as empty."""
    mock_chroma.return_value.get_collection.side_effect = ValueError("permission denied")

    with pytest.raises(ValueError, match="permission denied"):
        await get_knowledge_list()
