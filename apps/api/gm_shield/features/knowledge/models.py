"""
Pydantic schemas for the Knowledge feature slice.

Defines the request and response models used by the knowledge ingestion router.
"""

from typing import Optional
from pydantic import BaseModel, Field


class KnowledgeSourceCreate(BaseModel):
    """
    Payload for ingesting a new knowledge source document.

    The file must already exist on the local filesystem at the given path.
    Supported formats: `.pdf`, `.md`, `.txt`, `.csv`.
    """

    file_path: str = Field(
        ...,
        description="Absolute or relative path to the source file on the local filesystem. "
        "Supported formats: PDF (.pdf), Markdown (.md), plain text (.txt), CSV (.csv).",
        examples=["/data/uploads/monster-manual.pdf"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional human-readable label for this knowledge source.",
        examples=["D&D 5e Monster Manual"],
    )


class KnowledgeSourceResponse(BaseModel):
    """
    Response returned after a knowledge ingestion request is accepted.

    The document is processed asynchronously. Use the returned `task_id` to poll
    `GET /api/v1/tasks/{task_id}` for the processing status.
    """

    task_id: str = Field(
        ...,
        description="Unique identifier for the background processing task. "
        "Use this ID to poll task status.",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    status: str = Field(
        ...,
        description="Initial task status. Always `pending` on creation.",
        examples=["pending"],
    )
    message: str = Field(
        ...,
        description="Human-readable message describing the outcome of the request.",
        examples=["Processing started for monster-manual.pdf"],
    )


class KnowledgeSourceItem(BaseModel):
    """
    Summary of a single ingested knowledge source, derived from ChromaDB metadata.
    """

    source: str = Field(
        ...,
        description="Absolute path to the original source file.",
        examples=["/Users/gm/docs/monster-manual.pdf"],
    )
    filename: str = Field(
        ...,
        description="Basename of the source file.",
        examples=["monster-manual.pdf"],
    )
    chunk_count: int = Field(
        ...,
        description="Number of text chunks stored in ChromaDB for this source.",
        examples=[42],
    )


class KnowledgeListResponse(BaseModel):
    """Response for listing all ingested knowledge sources."""

    items: list[KnowledgeSourceItem] = Field(
        default_factory=list,
        description="All unique source documents currently indexed in ChromaDB.",
    )


class KnowledgeStatsResponse(BaseModel):
    """Aggregate statistics for the knowledge base."""

    document_count: int = Field(
        ...,
        description="Number of distinct source documents in the knowledge base.",
        examples=[12],
    )
    chunk_count: int = Field(
        ...,
        description="Total number of text chunks stored across all documents.",
        examples=[1420],
    )
