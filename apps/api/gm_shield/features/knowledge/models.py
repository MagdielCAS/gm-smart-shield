"""
Pydantic schemas for the Knowledge feature slice.

Defines the request and response models used by the knowledge ingestion router.
"""

from pydantic import BaseModel, Field
from typing import Optional


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
