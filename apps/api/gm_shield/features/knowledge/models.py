from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from gm_shield.shared.database.sqlite import Base


class KnowledgeSource(Base):
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

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def source(self) -> str:
        return self.file_path

    @property
    def filename(self) -> str:
        import os

        return os.path.basename(self.file_path)
