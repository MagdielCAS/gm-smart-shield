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
    },
)
async def add_knowledge_source(
    source: KnowledgeSourceCreate,
) -> KnowledgeSourceResponse:
    """
    Enqueue a document for ingestion into the vector knowledge base.

    The file at `source.file_path` is processed asynchronously.
    Returns a `task_id` that can be used to poll task status.
    """
    queue = get_task_queue()
    task_id = await queue.enqueue(process_knowledge_source, source.file_path)

    return KnowledgeSourceResponse(
        task_id=task_id,
        status="pending",
        message=f"Processing started for {source.file_path}",
    )
