"""
Reference feature — Data models.

Defines schemas for quick reference generation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReferenceRequest(BaseModel):
    """Request to generate quick references for a category."""

    category: str = Field(..., description="Category of reference (e.g., 'Spells', 'Classes', 'Races', 'Conditions').")
    source_id: str = Field(..., description="ID or filename of the uploaded rulebook.")


class ReferenceResponse(BaseModel):
    """Response containing the generated quick reference content."""

    category: str = Field(..., description="The category of the references.")
    content: str = Field(..., description="The generated reference content in Markdown format.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata.")
