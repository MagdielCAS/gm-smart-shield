"""
Notes feature — FastAPI router.

Exposes endpoints for note tagging.
"""

from fastapi import APIRouter, Depends
from gm_shield.features.notes.models import TaggingRequest, TaggingResponse
from gm_shield.features.notes.service import TaggingService, get_tagging_service

router = APIRouter()


@router.post("/tag", response_model=TaggingResponse, summary="Auto-Tag Note")
async def tag_note(request: TaggingRequest, service: TaggingService = Depends(get_tagging_service)):
    """
    Analyzes note content and extracts relevant tags and keywords.
    """
    return await service.tag_note(request.content)
