"""
HTTP integration tests for the knowledge list and stats endpoints.

Tests `GET /api/v1/knowledge/` and `GET /api/v1/knowledge/stats` using
FastAPI's TestClient, mocking the service layer.
"""

from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from gm_shield.main import app
from datetime import datetime

client = TestClient(app)


# ── GET /api/v1/knowledge/ ────────────────────────────────────────────────────


@patch("gm_shield.features.knowledge.router.get_knowledge_list", new_callable=AsyncMock)
def test_list_knowledge_sources_returns_items(mock_list):
    """Returns 200 with a list of ingested sources."""
    mock_list.return_value = [
        {
            "id": 1,
            "source": "/docs/rulebook.pdf",
            "filename": "rulebook.pdf",
            "chunk_count": 10,
            "status": "completed",
            "progress": 100.0,
            "current_step": "Done",
            "last_indexed_at": datetime(2023, 1, 1),
            "error_message": None,
            "features": ["indexation"],
        },
        {
            "id": 2,
            "source": "/docs/notes.txt",
            "filename": "notes.txt",
            "chunk_count": 5,
            "status": "running",
            "progress": 50.0,
            "current_step": "Embedding",
            "last_indexed_at": None,
            "error_message": None,
            "features": [],
        },
    ]

    response = client.get("/api/v1/knowledge/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    filenames = {i["filename"] for i in data["items"]}
    assert "rulebook.pdf" in filenames
    assert "notes.txt" in filenames

    # Check new fields
    item1 = next(i for i in data["items"] if i["filename"] == "rulebook.pdf")
    assert item1["status"] == "completed"
    assert item1["progress"] == 100.0


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


# ── POST still works ──────────────────────────────────────────────────────────


@patch("gm_shield.features.knowledge.router.create_or_update_knowledge_source")
@patch("gm_shield.features.knowledge.router.get_task_queue")
def test_post_knowledge_source_creates_db_record(mock_queue, mock_create):
    """Regression test — the POST ingest endpoint works and uses DB."""
    # Mock create/update to return an ID
    mock_create.return_value = 123

    queue = MagicMock()
    mock_queue.return_value = queue
    queue.enqueue = AsyncMock(return_value="task-xyz")

    response = client.post(
        "/api/v1/knowledge/",
        json={"file_path": "/docs/monsters.pdf"},
    )

    assert response.status_code == 202
    assert response.json()["task_id"] == "task-xyz"

    # Check interaction
    mock_create.assert_called_with("/docs/monsters.pdf")

    # Check queue enqueued with ID
    args, _ = queue.enqueue.call_args
    assert args[1] == 123  # ID, not path
