"""
Sheet feature — Data models.

Defines request/response schemas for character sheet operations.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SheetTemplateRequest(BaseModel):
    """Request to generate a character sheet template from a knowledge source."""

    source_id: str = Field(..., description="ID or filename of the uploaded rulebook (knowledge source).")
    system_name: Optional[str] = Field(None, description="Name of the RPG system (e.g. 'D&D 5e').")


class SheetTemplateResponse(BaseModel):
    """Response containing the generated character sheet template."""

    template_markdown: str = Field(..., description="The character sheet template in Markdown format.")
    frontmatter_schema: Dict[str, Any] = Field(..., description="JSON schema for the frontmatter properties.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the generation.")
