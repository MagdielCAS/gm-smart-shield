from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from gm_shield.core.config import settings

# Create engine for SQLite
# check_same_thread=False is needed for SQLite
engine = create_engine(
    settings.SQLITE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
