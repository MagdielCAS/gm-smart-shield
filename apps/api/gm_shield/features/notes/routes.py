"""
Notes feature — API router.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gm_shield.core.logging import get_logger
from gm_shield.features.notes import service
from gm_shield.features.notes.schemas import NoteCreate, NoteResponse, NoteUpdate
from gm_shield.shared.database.sqlite import get_db

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note."""
    return await service.create_note(db, note)


@router.get("/", response_model=List[NoteResponse])
def list_notes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all notes."""
    return service.list_notes(db, skip, limit)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific note by ID."""
    note = service.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int, note_update: NoteUpdate, db: Session = Depends(get_db)
):
    """
    Update a note.
    Triggers background auto-tagging if content changes.
    """
    note = await service.update_note(db, note_id, note_update)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    success = service.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
