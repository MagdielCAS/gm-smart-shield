"""
Database models for Character Sheets feature.
"""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from gm_shield.shared.database.sqlite import Base


class CharacterSheet(Base):
    """
    SQLAlchemy model representing a saved instance of a character sheet.
    """

    __tablename__ = "character_sheets"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("character_sheet_templates.id"), index=True
    )

    player_name: Mapped[str] = mapped_column(String, index=True)
    character_name: Mapped[str] = mapped_column(String, index=True)

    # Core stored content. Structure typically adheres to the associated template's schema.
    content: Mapped[dict] = mapped_column(JSON, default=dict)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
