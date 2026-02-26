"""
SQLAlchemy entities for the Notes feature slice.

Defines relational models for notes and note tags, including optional link
metadata that can reference extracted sources and page numbers.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gm_shield.shared.database.sqlite import Base


class Note(Base):
    """Primary notes table storing markdown content and optional frontmatter."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    frontmatter_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    folder_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tags: Mapped[list["NoteTag"]] = relationship(
        "NoteTag",
        back_populates="note",
        cascade="all, delete-orphan",
    )


class NoteTag(Base):
    """Secondary table linking notes to tags and optional source metadata."""

    __tablename__ = "note_tags"

    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(80), primary_key=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    note: Mapped[Note] = relationship("Note", back_populates="tags")
