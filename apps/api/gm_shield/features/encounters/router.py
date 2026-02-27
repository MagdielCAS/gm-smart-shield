"""
Encounter feature — FastAPI router.

Exposes endpoints for encounter generation.
"""

from fastapi import APIRouter, Depends
from gm_shield.features.encounters.models import EncounterRequest, EncounterResponse
from gm_shield.features.encounters.service import EncounterService, get_encounter_service

router = APIRouter()


@router.post("/generate", response_model=EncounterResponse, summary="Generate Encounter")
async def generate_encounter(request: EncounterRequest, service: EncounterService = Depends(get_encounter_service)):
    """
    Generates a creative encounter with NPCs and narrative description.

    The Encounter Agent uses the knowledge base to populate the encounter with appropriate monsters
    and setting details based on the request parameters.
    """
    return await service.generate_encounter(request.party_level, request.environment, request.difficulty, request.theme)
