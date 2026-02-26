from gm_shield.shared.database.sqlite import SessionLocal, Base, engine
from gm_shield.features.knowledge.models import KnowledgeSource
from datetime import datetime, timedelta, timezone


def seed():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    # 1. Completed item
    if (
        not session.query(KnowledgeSource)
        .filter_by(file_path="/docs/rulebook.pdf")
        .first()
    ):
        s1 = KnowledgeSource(
            file_path="/docs/rulebook.pdf",
            status="completed",
            progress=100.0,
            current_step="Done",
            chunk_count=42,
            last_indexed_at=datetime.now(timezone.utc),
            features=["indexation"],
        )
        session.add(s1)

    # 2. Running item
    if (
        not session.query(KnowledgeSource)
        .filter_by(file_path="/docs/new_monster.md")
        .first()
    ):
        s2 = KnowledgeSource(
            file_path="/docs/new_monster.md",
            status="running",
            progress=45.0,
            current_step="Embedding chunks (12/30)",
            chunk_count=0,
            started_at=datetime.now(timezone.utc) - timedelta(minutes=2),
            features=[],
        )
        session.add(s2)

    # 3. Failed item
    if (
        not session.query(KnowledgeSource)
        .filter_by(file_path="/docs/corrupted.csv")
        .first()
    ):
        s3 = KnowledgeSource(
            file_path="/docs/corrupted.csv",
            status="failed",
            progress=10.0,
            current_step="Extraction",
            chunk_count=0,
            error_message="File format not supported or corrupted",
            features=[],
        )
        session.add(s3)

    session.commit()
    session.close()
    print("Database seeded!")


if __name__ == "__main__":
    seed()
