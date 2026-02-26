"""
Chat feature — API routes.

Exposes the Query Agent endpoint which provides streaming RAG-based answers.
"""

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from gm_shield.core.logging import get_logger
from gm_shield.features.chat.models import ChatRequest
from gm_shield.features.chat.service import QueryAgent

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/query",
    summary="Ask a question to the Query Agent",
    description="Streams a markdown-formatted answer based on the knowledge base.",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
)
async def ask_query(request: ChatRequest):
    """
    Stream the answer chunk-by-chunk.

    Returns a raw text stream (`text/plain`) containing the Markdown response.
    """
    agent = QueryAgent()

    # StreamingResponse takes an async generator
    return StreamingResponse(
        agent.query(request.query),
        media_type="text/plain",
    )
