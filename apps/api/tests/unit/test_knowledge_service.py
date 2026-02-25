import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from gm_shield.main import app
from gm_shield.features.knowledge.service import process_knowledge_source

client = TestClient(app)

@pytest.fixture
def mock_queue():
    with patch("gm_shield.features.knowledge.router.get_task_queue") as mock:
        queue = AsyncMock()
        mock.return_value = queue
        queue.enqueue.return_value = "mock_task_id"
        yield queue

def test_add_knowledge_source(mock_queue):
    # Send a request to add a knowledge source
    response = client.post(
        "/api/v1/knowledge/",
        json={"file_path": "/path/to/test.pdf", "description": "Test PDF"}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "mock_task_id"
    assert data["status"] == "pending"
    assert "Processing started" in data["message"]

    # Check that the background task was enqueued
    mock_queue.enqueue.assert_called_once()
    args, _ = mock_queue.enqueue.call_args
    assert args[1] == "/path/to/test.pdf"

@patch("gm_shield.features.knowledge.service.extract_text_from_file")
@patch("gm_shield.features.knowledge.service.RecursiveCharacterTextSplitter")
@patch("gm_shield.features.knowledge.service.get_embedding_model")
@patch("gm_shield.features.knowledge.service.get_chroma_client")
@pytest.mark.asyncio
async def test_process_knowledge_source(mock_chroma, mock_embed, mock_split, mock_extract):
    mock_extract.return_value = "Chunk1 Chunk2 Chunk3"

    mock_splitter_instance = MagicMock()
    mock_splitter_instance.split_text.return_value = ["Chunk1", "Chunk2", "Chunk3"]
    mock_split.return_value = mock_splitter_instance

    mock_model = MagicMock()
    mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
    mock_embed.return_value = mock_model

    mock_collection = MagicMock()
    mock_chroma.return_value.get_or_create_collection.return_value = mock_collection

    result = await process_knowledge_source("/path/to/test.txt")

    assert "Processed 3 chunks" in result
    mock_extract.assert_called_with("/path/to/test.txt")
    mock_model.encode.assert_called_once()
    mock_collection.add.assert_called_once()
