"""
HTTP integration tests for the knowledge list and stats endpoints.

Tests `GET /api/v1/knowledge/` and `GET /api/v1/knowledge/stats` using
FastAPI's TestClient, mocking the ChromaDB service layer.
"""

from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from gm_shield.main import app

client = TestClient(app)


# ── GET /api/v1/knowledge/ ────────────────────────────────────────────────────


@patch("gm_shield.features.knowledge.router.get_knowledge_list", new_callable=AsyncMock)
def test_list_knowledge_sources_returns_items(mock_list):
    """Returns 200 with a list of ingested sources."""
    mock_list.return_value = [
        {"source": "/docs/rulebook.pdf", "filename": "rulebook.pdf", "chunk_count": 10},
        {"source": "/docs/notes.txt", "filename": "notes.txt", "chunk_count": 5},
    ]

    response = client.get("/api/v1/knowledge/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    filenames = {i["filename"] for i in data["items"]}
    assert "rulebook.pdf" in filenames
    assert "notes.txt" in filenames


@patch("gm_shield.features.knowledge.router.get_knowledge_list", new_callable=AsyncMock)
def test_list_knowledge_sources_empty(mock_list):
    """Returns 200 with an empty items list when no sources are ingested."""
    mock_list.return_value = []

    response = client.get("/api/v1/knowledge/")

    assert response.status_code == 200
    assert response.json() == {"items": []}


# ── GET /api/v1/knowledge/stats ───────────────────────────────────────────────


@patch(
    "gm_shield.features.knowledge.router.get_knowledge_stats", new_callable=AsyncMock
)
def test_knowledge_stats_returns_aggregates(mock_stats):
    """Returns 200 with correct aggregate statistics."""
    mock_stats.return_value = {"document_count": 3, "chunk_count": 75}

    response = client.get("/api/v1/knowledge/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["document_count"] == 3
    assert data["chunk_count"] == 75


@patch(
    "gm_shield.features.knowledge.router.get_knowledge_stats", new_callable=AsyncMock
)
def test_knowledge_stats_zero_when_empty(mock_stats):
    """Returns zeroes when the knowledge base is empty."""
    mock_stats.return_value = {"document_count": 0, "chunk_count": 0}

    response = client.get("/api/v1/knowledge/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["document_count"] == 0
    assert data["chunk_count"] == 0


# ── POST still works ──────────────────────────────────────────────────────────


@patch("gm_shield.features.knowledge.router.get_task_queue")
def test_post_knowledge_source_still_works(mock_queue):
    """Regression test — the original POST ingest endpoint still returns 202."""
    queue = MagicMock()
    mock_queue.return_value = queue
    queue.enqueue = AsyncMock(return_value="task-xyz")

    response = client.post(
        "/api/v1/knowledge/",
        json={"file_path": "/docs/monsters.pdf"},
    )

    assert response.status_code == 202
    assert response.json()["task_id"] == "task-xyz"
