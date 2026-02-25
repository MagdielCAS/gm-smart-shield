"""
SQLite database adapter — shared infrastructure.

Provides the SQLAlchemy engine, session factory, and the ``Base`` declarative class
that all feature-slice ORM models should inherit from.

Usage in a feature-slice model::

    from gm_shield.shared.database.sqlite import Base

    class Note(Base):
        __tablename__ = "notes"
        ...

Usage in a FastAPI dependency::

    from gm_shield.shared.database.sqlite import get_db

    @router.get("/notes")
    def list_notes(db: Session = Depends(get_db)):
        ...
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from gm_shield.core.config import settings

# ``check_same_thread=False`` is required for SQLite when the same connection
# is used across multiple threads (e.g. FastAPI with a thread-pool executor).
engine = create_engine(
    settings.SQLITE_URL,
    connect_args={"check_same_thread": False},
)

# Session factory — sessions are created per-request via the ``get_db`` dependency.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy ORM models.

    All feature-slice models must inherit from this class so that
    ``Base.metadata.create_all()`` in ``main.py`` picks them up.
    """


def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is closed.

    Use with ``Depends(get_db)`` in route handlers.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
