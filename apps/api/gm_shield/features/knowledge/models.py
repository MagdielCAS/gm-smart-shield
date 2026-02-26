from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from gm_shield.shared.database.sqlite import Base


class KnowledgeSource(Base):
    """
    SQLAlchemy model representing a knowledge source document and its processing state.

    Attributes:
        id (int): Primary key.
        file_path (str): Absolute path to the source file (unique).
        status (str): Current processing status (pending, running, completed, failed).
        progress (float): Completion percentage (0.0 - 100.0).
        current_step (str): Human-readable description of the current processing step.
        chunk_count (int): Number of chunks extracted and stored in ChromaDB.
        started_at (datetime): Timestamp when processing began.
        last_indexed_at (datetime): Timestamp when indexing successfully completed.
        error_message (str): Details of the last failure, if any.
        features (list): JSON list of enabled features (e.g. ["indexation"]).
        created_at (datetime): Record creation timestamp.
        updated_at (datetime): Record last update timestamp.
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

    @property
    def source(self) -> str:
        """Alias for file_path, used for API consistency."""
        return self.file_path

    @property
    def filename(self) -> str:
        """Extracts the filename from the full path."""
        import os

        return os.path.basename(self.file_path)
