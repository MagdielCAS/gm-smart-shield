"""
Pydantic schemas for the Notes feature slice.

Defines request and response contracts for creating, updating, and retrieving
GM notes with optional frontmatter metadata, tags, and source-link metadata.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NoteLinkMetadata(BaseModel):
    """Link metadata describing where a tagged note reference came from."""

    tag: str = Field(
        ...,
        description="Tag associated with the note link.",
        examples=["npc"],
    )
    source_id: str | None = Field(
        default=None,
        description="Optional knowledge/source identifier this tag originated from.",
        examples=["monster-manual"],
    )
    page_number: int | None = Field(
        default=None,
        description="Optional page number in the source document.",
        examples=[42],
    )


class NoteBasePayload(BaseModel):
    """Shared fields used by note creation and update payloads."""

    title: str = Field(
        ...,
        min_length=1,
        description="Human-friendly note title.",
        examples=["Session 12 recap"],
    )
    content: str = Field(
        ...,
        description="Markdown content for the note body.",
        examples=["# Session 12\nThe party arrived in Waterdeep."],
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Flat tag list for quick categorisation and filtering.",
        examples=[["session", "waterdeep"]],
    )
    campaign_id: str | None = Field(
        default=None,
        description="Optional frontmatter field for campaign scoping.",
        examples=["curse-of-strahd"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional frontmatter field for session scoping.",
        examples=["session-12"],
    )
    folder_id: int | None = Field(
        default=None,
        description="Optional folder identifier for note organisation.",
        examples=[3],
    )
    frontmatter: dict[str, Any] | None = Field(
        default=None,
        description="Optional free-form frontmatter metadata.",
        examples=[{"location": "Yawning Portal", "mood": "tense"}],
    )


class NoteCreateRequest(NoteBasePayload):
    """Payload for creating a new note."""


class NoteUpdateRequest(NoteBasePayload):
    """Payload for replacing an existing note."""


class NoteResponse(BaseModel):
    """API response schema representing a note resource."""

    id: int = Field(..., description="Unique note identifier.", examples=[7])
    title: str = Field(..., description="Note title.")
    content: str = Field(..., description="Markdown note body.")
    frontmatter: dict[str, Any] | None = Field(
        default=None,
        description="Optional frontmatter metadata stored with the note.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized extracted metadata derived from note content.",
    )
    folder_id: int | None = Field(
        default=None,
        description="Optional folder identifier linked to the note.",
    )
    created_at: datetime = Field(..., description="UTC timestamp when the note was created.")
    updated_at: datetime = Field(..., description="UTC timestamp when the note was last updated.")
    tags: list[str] = Field(
        default_factory=list,
        description="All tags associated with the note.",
    )
    links: list[NoteLinkMetadata] = Field(
        default_factory=list,
        description="Link metadata associated with note tags.",
    )


class NoteListResponse(BaseModel):
    """Response schema for listing notes."""

    items: list[NoteResponse] = Field(default_factory=list, description="Collection of notes.")
