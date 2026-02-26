from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from gm_shield.shared.database.sqlite import Base


class KnowledgeSource(Base):
    """
    SQLAlchemy model representing a knowledge source document and its processing state.
    """

    __tablename__ = "knowledge_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_path: Mapped[str] = mapped_column(String, unique=True, index=True)

    # Task metadata
    status: Mapped[str] = mapped_column(
        String, default="pending"
    )  # pending, running, completed, failed
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    current_step: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Result metadata
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Features (stored as JSON list of strings, e.g. ["indexation", "extraction"])
    features: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class QuickReference(Base):
    """
    Extracted reference items (spells, weapons, items, feats) from knowledge sources.
    """
    __tablename__ = "quick_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(Integer, index=True)  # FK to KnowledgeSource

    # Core Data
    name: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)  # e.g., "Spell", "Weapon"
    description: Mapped[str] = mapped_column(Text)

    # Metadata
    tags: Mapped[Optional[list]] = mapped_column(JSON) # e.g. ["Fire", "Level 1"]

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    @property
    def source(self) -> str:
        """Alias for file_path, used for API consistency."""
        return self.file_path

    @property
    def filename(self) -> str:
        """Extracts the filename from the full path."""
        import os

        return os.path.basename(self.file_path)


class CharacterSheetTemplate(Base):
    """
    Extracted character sheet structure from a rulebook.
    """
    __tablename__ = "character_sheet_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(Integer, index=True)  # FK to KnowledgeSource

    # Metadata
    name: Mapped[str] = mapped_column(String)  # e.g. "D&D 5e Character Sheet"
    system: Mapped[str] = mapped_column(String) # e.g. "D&D 5e"

    # The actual schema/template content (YAML or JSON structure)
    template_schema: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
