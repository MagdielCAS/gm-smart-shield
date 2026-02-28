"""
Notes feature — service logic.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from gm_shield.core.logging import get_logger
from gm_shield.features.notes.agents.tagger import TaggingAgent
from gm_shield.features.notes.models import Note, NoteTag
from gm_shield.features.notes.schemas import NoteCreate, NoteUpdate
from gm_shield.shared.database.sqlite import SessionLocal
from gm_shield.shared.worker.memory import get_task_queue

logger = get_logger(__name__)


def get_note(db: Session, note_id: int) -> Optional[Note]:
    """Get a single note by ID."""
    return db.query(Note).filter(Note.id == note_id).first()


def list_notes(db: Session, skip: int = 0, limit: int = 100) -> List[Note]:
    """List notes, ordered by most recently updated."""
    return (
        db.query(Note).order_by(Note.updated_at.desc()).offset(skip).limit(limit).all()
    )


def create_note(db: Session, note: NoteCreate) -> Note:
    """Create a new note."""
    db_note = Note(title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


async def update_note(
    db: Session, note_id: int, note_update: NoteUpdate
) -> Optional[Note]:
    """Update an existing note."""
    db_note = get_note(db, note_id)
    if not db_note:
        return None

    update_data = note_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_note, key, value)

    db.commit()
    db.refresh(db_note)

    if "content" in update_data:
        queue = get_task_queue()
        await queue.enqueue(run_auto_tagging, note_id)

    return db_note


def delete_note(db: Session, note_id: int) -> bool:
    """Delete a note."""
    db_note = get_note(db, note_id)
    if not db_note:
        return False

    db.delete(db_note)
    db.commit()
    return True


async def run_auto_tagging(note_id: int):
    """
    Background task to auto-tag a note.
    """
    logger.info("auto_tagging_started", note_id=note_id)
    session = SessionLocal()
    try:
        note = session.query(Note).filter(Note.id == note_id).first()
        if not note:
            logger.warning("auto_tagging_note_not_found", note_id=note_id)
            return

        agent = TaggingAgent()
        tags = await agent.extract_tags(note.content)

        if tags:
            # Replace existing tags
            session.query(NoteTag).filter(NoteTag.note_id == note_id).delete()

            for tag in tags:
                session.add(NoteTag(note_id=note_id, tag=tag))

            session.commit()
            logger.info("auto_tagging_complete", note_id=note_id, tag_count=len(tags))
        else:
            logger.info("auto_tagging_no_tags", note_id=note_id)

    except Exception as e:
        logger.error("auto_tagging_failed", note_id=note_id, error=str(e))
        session.rollback()
    finally:
        session.close()
