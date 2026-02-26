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
    source_file: str | None = Field(
        default=None,
        description="Optional source file path for the linked chunk.",
        examples=["/data/rules/monster-manual.pdf"],
    )
    page_number: int | None = Field(
        default=None,
        description="Optional page number in the source document.",
        examples=[42],
    )
    chunk_id: str | None = Field(
        default=None,
        description="Optional Chroma chunk/document identifier for the source.",
        examples=["monster-manual_a1b2c3d4_7"],
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
    sources: list[NoteLinkMetadata] = Field(
        default_factory=list,
        description="Accepted structured source links associated with this note.",
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
    created_at: datetime = Field(
        ..., description="UTC timestamp when the note was created."
    )
    updated_at: datetime = Field(
        ..., description="UTC timestamp when the note was last updated."
    )
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

    items: list[NoteResponse] = Field(
        default_factory=list, description="Collection of notes."
    )


class NoteLinkSuggestionRequest(BaseModel):
    """Payload requesting link suggestions for a note."""

    limit: int = Field(
        default=5, ge=1, le=20, description="Maximum number of suggested links."
    )


class NoteLinkSuggestion(BaseModel):
    """A suggested link candidate derived from knowledge chunks."""

    source_id: str | None = Field(
        default=None, description="Best-effort source identifier."
    )
    source_file: str | None = Field(
        default=None, description="Best-effort source file path."
    )
    page_number: int | None = Field(
        default=None, description="Best-effort source page number."
    )
    chunk_id: str | None = Field(
        default=None, description="Suggested Chroma chunk identifier."
    )
    snippet: str = Field(
        ..., description="Chunk text snippet used for suggestion context."
    )
    similarity_score: float = Field(
        ..., description="Semantic similarity score in range [0,1]."
    )
    keyword_overlap: int = Field(
        ..., description="Count of overlapping keywords with note content."
    )


class NoteLinkSuggestionResponse(BaseModel):
    """Response payload containing suggested links for a note."""

    note_id: int = Field(
        ..., description="Note identifier used to generate suggestions."
    )
    suggestions: list[NoteLinkSuggestion] = Field(
        default_factory=list, description="Suggested source links."
    )


class NoteInlineSuggestionRequest(BaseModel):
    """Payload requesting ghost-text suggestions while editing a note."""

    content: str = Field(..., description="Current full editor content.")
    cursor_index: int = Field(
        ..., ge=0, description="Current cursor location within content."
    )


class NoteInlineSuggestionResponse(BaseModel):
    """Response payload for inline ghost-text suggestions."""

    suggestion: str = Field(
        default="", description="Suggested text to insert at the cursor."
    )
    reason: str = Field(
        default="none",
        description="Reason category for debugging: punctuation, newline, idle, or none.",
    )


class NoteTransformAction(str):
    """Enum-like string literals for context menu transformation actions."""

    REWRITE = "rewrite"
    FORMAT = "format"
    MAKE_DRAMATIC = "make_dramatic"
    GENERATE_CONTENT = "generate_content"
    ADD_REFERENCE_LINK = "add_reference_link"
    SEARCH_REFERENCE_LINK = "search_reference_link"


class NoteTransformRequest(BaseModel):
    """Payload requesting non-destructive context transformations."""

    action: str = Field(..., description="Requested transformation action.")
    content: str = Field(..., description="Current full editor content.")
    selection_start: int = Field(
        ..., ge=0, description="Selection start index in the editor content."
    )
    selection_end: int = Field(
        ..., ge=0, description="Selection end index in the editor content."
    )


class NoteTransformResponse(BaseModel):
    """Preview payload for a context-action transformation."""

    action: str = Field(
        ..., description="Transformation action that produced this preview."
    )
    original_text: str = Field(
        ..., description="Original selected text before transformation."
    )
    preview_text: str = Field(
        ..., description="Suggested replacement or insertion text."
    )
    selection_start: int = Field(
        ..., ge=0, description="Selection start index used by the action."
    )
    selection_end: int = Field(
        ..., ge=0, description="Selection end index used by the action."
    )
    mode: str = Field(
        default="replace",
        description="How to apply preview: replace or insert.",
    )


class NoteFolderCreateRequest(BaseModel):
    """Payload for creating a note folder/notebook."""

    name: str = Field(
        ...,
        min_length=1,
        description="Folder display name.",
        examples=["Session Notes"],
    )
    parent_id: int | None = Field(
        default=None,
        description="Optional parent folder ID for nested structures.",
        examples=[1],
    )


class NoteFolderResponse(BaseModel):
    """Response schema describing a note folder/notebook."""

    id: int = Field(..., description="Unique folder identifier.", examples=[3])
    name: str = Field(..., description="Folder display name.")
    parent_id: int | None = Field(
        default=None,
        description="Optional parent folder ID.",
    )


class NoteFolderListResponse(BaseModel):
    """Response payload listing folders."""

    items: list[NoteFolderResponse] = Field(
        default_factory=list,
        description="All available note folders.",
    )
