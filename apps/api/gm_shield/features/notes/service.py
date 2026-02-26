"""
Business logic for the Notes feature slice.

Provides CRUD operations for note records and related tags while keeping route
handlers thin and focused on HTTP concerns.
"""

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from gm_shield.features.notes.entities import Note, NoteTag
from gm_shield.features.notes.models import (
    NoteCreateRequest,
    NoteLinkMetadata,
    NoteResponse,
    NoteUpdateRequest,
)


def _to_response(note: Note) -> NoteResponse:
    """Convert a ``Note`` ORM entity to an API response schema."""
    parsed_frontmatter = json.loads(note.frontmatter_json) if note.frontmatter_json else None
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content_markdown,
        frontmatter=parsed_frontmatter,
        folder_id=note.folder_id,
        created_at=note.created_at,
        updated_at=note.updated_at,
        tags=[tag.tag for tag in note.tags],
        links=[
            NoteLinkMetadata(tag=tag.tag, source_id=tag.source_id, page_number=tag.page_number)
            for tag in note.tags
        ],
    )


def create_note(db: Session, payload: NoteCreateRequest) -> NoteResponse:
    """
    Create and persist a new note.

    Args:
        db: Active SQLAlchemy session.
        payload: Incoming note creation payload.

    Returns:
        Created note as a response schema.
    """
    frontmatter = payload.frontmatter or {}
    if payload.campaign_id is not None:
        frontmatter.setdefault("campaign_id", payload.campaign_id)
    if payload.session_id is not None:
        frontmatter.setdefault("session_id", payload.session_id)

    note = Note(
        title=payload.title,
        content_markdown=payload.content,
        frontmatter_json=json.dumps(frontmatter) if frontmatter else None,
        folder_id=payload.folder_id,
    )
    note.tags = [NoteTag(tag=tag) for tag in payload.tags]

    db.add(note)
    db.commit()
    db.refresh(note)
    return _to_response(note)


def list_notes(db: Session) -> list[NoteResponse]:
    """
    List all notes sorted by newest update first.

    Args:
        db: Active SQLAlchemy session.

    Returns:
        Ordered list of note response objects.
    """
    notes = db.query(Note).order_by(Note.updated_at.desc(), Note.id.desc()).all()
    return [_to_response(note) for note in notes]


def get_note(db: Session, note_id: int) -> NoteResponse:
    """
    Retrieve a note by ID.

    Args:
        db: Active SQLAlchemy session.
        note_id: Note identifier.

    Returns:
        Retrieved note schema.

    Raises:
        HTTPException: If no note exists for ``note_id``.
    """
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return _to_response(note)


def update_note(db: Session, note_id: int, payload: NoteUpdateRequest) -> NoteResponse:
    """
    Replace an existing note and bump the ``updated_at`` timestamp.

    Args:
        db: Active SQLAlchemy session.
        note_id: Note identifier.
        payload: Replacement note payload.

    Returns:
        Updated note schema.

    Raises:
        HTTPException: If no note exists for ``note_id``.
    """
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    frontmatter = payload.frontmatter or {}
    if payload.campaign_id is not None:
        frontmatter.setdefault("campaign_id", payload.campaign_id)
    if payload.session_id is not None:
        frontmatter.setdefault("session_id", payload.session_id)

    note.title = payload.title
    note.content_markdown = payload.content
    note.folder_id = payload.folder_id
    note.frontmatter_json = json.dumps(frontmatter) if frontmatter else None
    note.updated_at = datetime.now(timezone.utc)

    note.tags.clear()
    note.tags.extend(NoteTag(tag=tag) for tag in payload.tags)

    db.commit()
    db.refresh(note)
    return _to_response(note)


def delete_note(db: Session, note_id: int) -> None:
    """
    Delete an existing note.

    Args:
        db: Active SQLAlchemy session.
        note_id: Note identifier.

    Raises:
        HTTPException: If no note exists for ``note_id``.
    """
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    db.delete(note)
    db.commit()
