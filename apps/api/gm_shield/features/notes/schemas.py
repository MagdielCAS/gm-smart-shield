"""
Notes feature — Pydantic schemas.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NoteTagResponse(BaseModel):
    id: int
    tag: str
    source_link: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class NoteBase(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(default="")


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    content: Optional[str] = None


class NoteResponse(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: List[NoteTagResponse] = []

    model_config = ConfigDict(from_attributes=True)
