"""
Shared Pydantic schemas for LLM agents.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class CharacterSheetSchema(BaseModel):
    """Structured output for character sheet extraction."""

    system_name: str = Field(
        description="The name of the RPG system (e.g., 'D&D 5e', 'Pathfinder 2e')."
    )
    template_name: str = Field(
        description="A descriptive name for the template (e.g., 'Standard Character Sheet')."
    )
    sections: Dict[str, Any] = Field(
        description="A dictionary representing the sections of the character sheet (e.g., Attributes, Skills, Equipment). Keys are section names, values are lists of fields or nested structures."
    )
