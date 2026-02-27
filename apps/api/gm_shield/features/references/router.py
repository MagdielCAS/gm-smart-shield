"""
Reference feature — FastAPI router.

Exposes endpoints for quick reference generation.
"""

from fastapi import APIRouter, Depends
from gm_shield.features.references.models import ReferenceRequest, ReferenceResponse
from gm_shield.features.references.service import ReferenceService, get_reference_service

router = APIRouter()


@router.post("/generate", response_model=ReferenceResponse, summary="Generate Quick References")
async def generate_references(request: ReferenceRequest, service: ReferenceService = Depends(get_reference_service)):
    """
    Generates quick reference summaries for a given category (e.g., Spells, Classes).
    """
    return await service.generate_reference(request.category, request.source_id)
