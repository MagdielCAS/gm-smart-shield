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

# SQLite requires check_same_thread=False when used with a multi-threaded server
# (e.g. FastAPI with a thread-pool executor).
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

    pass


def get_db():
    """
    Yield a SQLAlchemy database session.

    Intended for use as a FastAPI dependency. The session is always closed after
    the request completes, whether or not an exception is raised.

    Yields:
        Session: An active SQLAlchemy ``Session`` bound to the configured SQLite engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
