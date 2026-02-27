"""
Encounter feature — Data models.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EncounterRequest(BaseModel):
    """Request to generate an encounter."""

    party_level: int = Field(..., description="Average level of the party.")
    environment: str = Field(..., description="Setting (e.g., Forest, Dungeon).")
    difficulty: str = Field("Medium", description="Difficulty (Easy, Medium, Hard, Deadly).")
    theme: Optional[str] = Field(None, description="Theme or specific monsters to include.")


class EncounterResponse(BaseModel):
    """Response containing the generated encounter."""

    title: str = Field(..., description="A creative title for the encounter.")
    description: str = Field(..., description="Narrative description.")
    tactics: str = Field(..., description="Enemy tactics and behavior.")
    npc_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Simplified stat blocks for NPCs.")
    loot: Optional[str] = Field(None, description="Suggested loot.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata.")
