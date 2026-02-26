"""
Chat feature — FastAPI router.

Provides endpoints for interacting with the Query Agent.
"""

from fastapi import APIRouter, Depends
from gm_shield.features.chat.models import ChatRequest, ChatResponse
from gm_shield.features.chat.service import ChatService, get_chat_service

router = APIRouter()


@router.post("/", response_model=ChatResponse, summary="Chat with the Query Agent")
async def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """
    Ask a question against the loaded knowledge base.

    The Query Agent will search for relevant context and provide a grounded answer.
    """
    return await service.get_response(request.query)
