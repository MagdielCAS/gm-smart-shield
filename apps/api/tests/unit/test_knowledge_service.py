"""
Unit tests for knowledge processing service.

Tests the `process_knowledge_source` async pipeline, ensuring that:
1. Database status is updated at each step (Extraction, Chunking, Embedding, Storage).
2. External services (ChromaDB, SentenceTransformer) are called correctly.
3. Errors are caught and recorded in the database.
"""

import pytest
from unittest.mock import MagicMock, patch
from gm_shield.features.knowledge.service import (
    process_knowledge_source,
    delete_knowledge_source,
)


# ── Fixtures & Mocks ──────────────────────────────────────────────────────────


@pytest.fixture
def mock_db_session():
    """Mock the SQLAlchemy session used within the service."""
    with patch("gm_shield.features.knowledge.service.SessionLocal") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_external_services():
    """Patch all external heavy dependencies (PDF, ML models, ChromaDB)."""
    with (
        patch("gm_shield.features.knowledge.service.extract_text_from_file") as extract,
        patch(
            "gm_shield.features.knowledge.service.RecursiveCharacterTextSplitter"
        ) as splitter,
        patch("gm_shield.features.knowledge.service.get_embedding_model") as embed,
        patch("gm_shield.features.knowledge.service.get_chroma_client") as chroma,
    ):
        # Setup default successful behaviors
        extract.return_value = "Chunk1 Chunk2 Chunk3"

        splitter_instance = MagicMock()
        splitter_instance.split_text.return_value = ["Chunk1", "Chunk2", "Chunk3"]
        splitter.return_value = splitter_instance

        model_instance = MagicMock()
        model_instance.encode.return_value = MagicMock(
            tolist=lambda: [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        )
        embed.return_value = model_instance

        collection = MagicMock()
        chroma.return_value.get_or_create_collection.return_value = collection

        yield {
            "extract": extract,
            "splitter": splitter_instance,
            "embed": model_instance,
            "collection": collection,
        }


# ── process_knowledge_source ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_knowledge_source_success(
    mock_db_session, mock_external_services
):
    """
    Test the happy path:
    - Retrieves source from DB.
    - Updates status to 'running'.
    - Extracts, Chunks, Embeds, Stores.
    - Updates status to 'completed'.
    """
    # Mock DB record
    source_record = MagicMock()
    source_record.id = 1
    source_record.file_path = "/docs/rulebook.pdf"
    source_record.features = []  # Initialize as empty list so `if not features` works
    # The service queries the DB multiple times. ensure it finds the record.
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        source_record
    )

    # Run
    result = await process_knowledge_source(1)

    # Verify result string
    assert "Processed 3 chunks" in result

    # Verify DB interactions
    # 1. Initial lookup
    # 2. Status update to running
    # 3. Progress updates
    # 4. Final completion update
    assert source_record.status == "completed"
    assert source_record.progress == 100.0
    assert source_record.chunk_count == 3
    assert source_record.features == ["indexation"]

    # Verify external calls
    mock_external_services["extract"].assert_called_with("/docs/rulebook.pdf")
    mock_external_services["collection"].add.assert_called_once()


@pytest.mark.asyncio
async def test_process_knowledge_source_not_found(mock_db_session):
    """If the source ID is not found in DB, return error string."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = await process_knowledge_source(999)

    assert result == "Source not found"


@pytest.mark.asyncio
async def test_process_knowledge_source_extraction_failure(
    mock_db_session, mock_external_services
):
    """If extraction fails (or returns empty), status is set to 'failed'."""
    # Mock DB record
    source_record = MagicMock()
    source_record.file_path = "/docs/empty.txt"
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        source_record
    )

    # Mock extraction returning empty string
    mock_external_services["extract"].return_value = ""

    result = await process_knowledge_source(1)

    assert "No text content found" in result

    # Verify DB failure state - note that `_update_task_state` re-queries the object
    # but since we mock the query return value to be the SAME object instance,
    # we can check that instance.
    # Actually `_update_task_state` does a fresh query.
    # We must ensure the fresh query returns our mock object.

    # In the service code, `_update_task_state` calls `session.commit()`.
    # We can check if `status` was set to failed on our mock object (since it's returned by the query).

    # However, `_update_task_state` is called with a NEW session in the real code?
    # No, `_process_sync` creates ONE session and passes it to `_update_task_state`.
    # Wait, `_update_task_state` takes `session` as arg.

    # But `_process_sync` does:
    # session = SessionLocal()
    # ...
    # _update_task_state(session, ...)

    # So yes, it uses the mocked session.

    # But wait, `_update_task_state` re-queries:
    # source = session.query(KnowledgeSource).filter(...).first()

    # So `source_record` must be returned by that query.
    assert source_record.status == "failed"
    assert "No text content found" in source_record.error_message


@pytest.mark.asyncio
async def test_process_knowledge_source_exception_handling(
    mock_db_session, mock_external_services
):
    """Any unhandled exception during processing sets status to 'failed'."""
    source_record = MagicMock()
    source_record.file_path = "/docs/broken.pdf"
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        source_record
    )

    # Force an exception during extraction
    mock_external_services["extract"].side_effect = Exception("Corrupted file")

    result = await process_knowledge_source(1)

    assert "Failed: Corrupted file" in result
    assert source_record.status == "failed"
    assert "Corrupted file" in source_record.error_message


@pytest.mark.asyncio
async def test_process_knowledge_source_does_not_delete_on_add_failure(
    mock_db_session, mock_external_services
):
    """Existing vectors are preserved if replacement write fails."""
    source_record = MagicMock()
    source_record.file_path = "/docs/rulebook.pdf"
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        source_record
    )

    collection = mock_external_services["collection"]
    collection.get.return_value = {"ids": ["old_chunk_1", "old_chunk_2"]}
    collection.add.side_effect = RuntimeError("Transient Chroma error")

    result = await process_knowledge_source(1)

    assert "Failed: Transient Chroma error" in result
    collection.delete.assert_not_called()
    assert source_record.status == "failed"
    assert "Transient Chroma error" in source_record.error_message


# ── delete_knowledge_source ──────────────────────────────────────────────────


def test_delete_knowledge_source_success(mock_db_session, mock_external_services):
    """It deletes records from SQLite and ChromaDB."""
    source_record = MagicMock()
    source_record.id = 1
    source_record.file_path = "/docs/to_delete.pdf"
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        source_record
    )

    collection = mock_external_services["collection"]
    collection.get.return_value = {"ids": ["chunk_1", "chunk_2"]}

    delete_knowledge_source(1)

    collection.get.assert_called_once_with(
        where={"source": "/docs/to_delete.pdf"}, include=[]
    )
    collection.delete.assert_called_once_with(ids=["chunk_1", "chunk_2"])
    mock_db_session.delete.assert_called_once_with(source_record)
    mock_db_session.commit.assert_called_once()


def test_delete_knowledge_source_not_found(mock_db_session):
    """It raises ValueError if the source doesn't exist."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Source 999 not found"):
        delete_knowledge_source(999)
