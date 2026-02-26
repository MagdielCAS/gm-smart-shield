"""
Knowledge feature — HTTP router.

Handles document ingestion requests and knowledge base queries.
All heavy processing (text extraction, chunking, embedding, ChromaDB storage)
runs asynchronously in the background via the task queue so that the HTTP
response is returned immediately.
"""

from fastapi import APIRouter, status
from gm_shield.features.knowledge.models import (
    KnowledgeListResponse,
    KnowledgeSourceCreate,
    KnowledgeSourceItem,
    KnowledgeSourceResponse,
    KnowledgeStatsResponse,
)
from gm_shield.features.knowledge.service import (
    get_knowledge_list,
    get_knowledge_stats,
    process_knowledge_source,
)
from gm_shield.shared.worker.memory import get_task_queue

router = APIRouter()


@router.post(
    "/",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a knowledge source document",
    description=(
        "Accepts a file path and enqueues an asynchronous ingestion job.\n\n"
        "**Processing pipeline (runs in background):**\n"
        "1. Extract text from the file (PDF / Markdown / TXT / CSV)\n"
        "2. Split text into overlapping chunks (~1 000 tokens each)\n"
        "3. Embed chunks with `all-MiniLM-L6-v2` (sentence-transformers)\n"
        "4. Store embeddings in ChromaDB under the `knowledge_base` collection\n\n"
        "Poll `GET /api/v1/tasks/{task_id}` to track processing progress."
    ),
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Ingestion task accepted and enqueued successfully."
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Validation error — file_path is missing or malformed."
        },
    },
)
async def add_knowledge_source(source: KnowledgeSourceCreate):
    """
    Accept a file for ingestion into the knowledge base.

    The file is **not** processed synchronously. Instead, a background task is
    enqueued that will:
    1. Extract raw text from the file (PDF, Markdown, plain text, or CSV).
    2. Split the text into overlapping chunks (~1 000 tokens).
    3. Generate vector embeddings using `all-MiniLM-L6-v2`.
    4. Store the chunks and embeddings in ChromaDB under the `knowledge_base` collection.

    Returns a `task_id` that can be used to poll the processing status via
    `GET /api/v1/tasks/{task_id}` (when that endpoint is available).
    """
    queue = get_task_queue()
    task_id = await queue.enqueue(process_knowledge_source, source.file_path)

    return KnowledgeSourceResponse(
        task_id=task_id,
        status="pending",
        message=f"Processing started for {source.file_path}",
    )


@router.get(
    "/",
    response_model=KnowledgeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all ingested knowledge sources",
    description=(
        "Returns all unique source documents currently stored in the ChromaDB "
        "`knowledge_base` collection, grouped by file path.\n\n"
        "Each item includes the source path, filename, and the number of text "
        "chunks stored for that document."
    ),
)
async def list_knowledge_sources():
    """
    List all distinct knowledge source documents in the vector store.

    Results are derived from ChromaDB chunk metadata and grouped by source file.
    Returns an empty list when no documents have been ingested yet.
    """
    raw = await get_knowledge_list()
    items = [KnowledgeSourceItem(**entry) for entry in raw]
    return KnowledgeListResponse(items=items)


@router.get(
    "/stats",
    response_model=KnowledgeStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Knowledge base aggregate statistics",
    description=(
        "Returns aggregate statistics for the knowledge base: total distinct "
        "documents and total chunk count stored in ChromaDB."
    ),
)
async def knowledge_stats():
    """Return aggregate statistics for the ChromaDB knowledge base collection."""
    stats = await get_knowledge_stats()
    return KnowledgeStatsResponse(**stats)
