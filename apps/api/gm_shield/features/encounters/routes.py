"""
Encounter Generator API Routes.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Import Service
from gm_shield.features.encounters.service import EncounterAgent, EncounterResponse

router = APIRouter(prefix="/encounters", tags=["encounters"])

class EncounterRequest(BaseModel):
    level: str
    difficulty: str
    theme: str

@router.post("/generate", response_model=EncounterResponse)
async def generate_encounter(request: EncounterRequest):
    """
    Generate a complete encounter using the Encounter Agent.
    This may take 10-20 seconds.
    """
    agent = EncounterAgent()

    try:
        response = await agent.generate_encounter(
            level=request.level,
            difficulty=request.difficulty,
            theme=request.theme
        )

        if not response:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate encounter. The LLM response was empty or malformed."
            )

        return response

    except Exception as e:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encounter generation error: {str(e)}"
        )
