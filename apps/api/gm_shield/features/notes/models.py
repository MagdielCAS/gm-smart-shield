"""
Notes feature — Data models for tagging.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class TaggingRequest(BaseModel):
    """Request to generate tags for a note."""

    content: str = Field(..., description="The content of the note to analyze.")


class TaggingResponse(BaseModel):
    """Response containing generated tags and keywords."""

    tags: List[str] = Field(..., description="List of relevant tags (e.g., 'NPC', 'Location').")
    keywords: List[str] = Field(..., description="Specific keywords found in the text.")
    suggested_links: List[Dict[str, str]] = Field(default_factory=list, description="Potential links to knowledge base entries.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata.")
