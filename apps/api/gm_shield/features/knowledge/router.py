"""
Knowledge feature — HTTP router.

Handles document ingestion requests. All heavy processing (text extraction,
chunking, embedding, ChromaDB storage) runs asynchronously in the background
via the task queue so that the HTTP response is returned immediately.
"""

from fastapi import APIRouter, status
from gm_shield.features.knowledge.models import (
    KnowledgeSourceCreate,
    KnowledgeSourceResponse,
)
from gm_shield.features.knowledge.service import process_knowledge_source
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
