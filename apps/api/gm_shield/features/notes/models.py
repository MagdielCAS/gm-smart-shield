"""
Notes feature — database models.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gm_shield.shared.database.sqlite import Base


class Note(Base):
    """
    User-created note.
    """

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, default="Untitled Note")
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tags: Mapped[List["NoteTag"]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )


class NoteTag(Base):
    """
    Tags extracted from notes or manually added.
    May link back to a source document in the knowledge base.
    """

    __tablename__ = "note_tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id"))
    tag: Mapped[str] = mapped_column(String, index=True)
    source_link: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Source file reference if any"
    )

    note: Mapped["Note"] = relationship(back_populates="tags")
