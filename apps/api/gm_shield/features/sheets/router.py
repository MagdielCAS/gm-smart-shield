"""
Sheet feature — FastAPI router.

Exposes endpoints for character sheet template generation.
"""

from fastapi import APIRouter, Depends
from gm_shield.features.sheets.models import SheetTemplateRequest, SheetTemplateResponse
from gm_shield.features.sheets.service import SheetService, get_sheet_service

router = APIRouter()


@router.post("/generate", response_model=SheetTemplateResponse, summary="Generate Character Sheet Template")
async def generate_template(request: SheetTemplateRequest, service: SheetService = Depends(get_sheet_service)):
    """
    Extracts a character sheet template from a knowledge source (rulebook).

    The Sheet Agent scans the rulebook for character creation rules and returns a structured Markdown template.
    """
    return await service.generate_template(request.source_id, request.system_name)
