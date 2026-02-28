"""
Unit tests for knowledge service list & stats functions.

Tests `get_knowledge_list` and `get_knowledge_stats` by mocking the SQLite session,
ensuring correct data mapping and aggregate calculations.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from gm_shield.features.knowledge.service import (
    get_knowledge_list,
    get_knowledge_stats,
)


@patch("gm_shield.features.knowledge.service.SessionLocal")
@pytest.mark.asyncio
async def test_get_knowledge_list_returns_sources(mock_session_cls):
    """Sources are retrieved from SQLite and mapped to dicts."""
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session

    # Mock source objects
    s1 = MagicMock()
    s1.id = 1
    s1.file_path = "/docs/rulebook.pdf"
    s1.chunk_count = 10
    s1.status = "completed"
    s1.progress = 100.0
    s1.current_step = "Done"
    s1.last_indexed_at = datetime(2023, 1, 1)
    s1.error_message = None
    s1.features = ["indexation"]

    s2 = MagicMock()
    s2.id = 2
    s2.file_path = "/docs/notes.txt"
    s2.chunk_count = 5
    s2.status = "running"
    s2.progress = 50.0
    s2.current_step = "Embedding"
    s2.last_indexed_at = None
    s2.error_message = None
    s2.features = []

    mock_session.query.return_value.order_by.return_value.all.return_value = [s1, s2]

    result = await get_knowledge_list()

    assert len(result) == 2
    assert result[0]["source"] == "/docs/rulebook.pdf"
    assert result[0]["chunk_count"] == 10
    assert result[0]["status"] == "completed"

    assert result[1]["source"] == "/docs/notes.txt"
    assert result[1]["status"] == "running"


@patch("gm_shield.features.knowledge.service.SessionLocal")
@pytest.mark.asyncio
async def test_get_knowledge_stats_aggregates_correctly(mock_session_cls):
    """Stats correctly count distinct documents and total chunks."""
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session

    mock_session.query.return_value.count.return_value = 2
    mock_session.query.return_value.with_entities.return_value.all.return_value = [
        (10,),
        (5,),
    ]

    stats = await get_knowledge_stats()

    assert stats["document_count"] == 2
    assert stats["chunk_count"] == 15
