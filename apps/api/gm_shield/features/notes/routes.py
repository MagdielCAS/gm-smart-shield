"""
FastAPI routes for the Notes feature slice.

Exposes CRUD endpoints for user-authored notes under the API v1 namespace.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from gm_shield.features.notes.models import (
    NoteCreateRequest,
    NoteListResponse,
    NoteResponse,
    NoteUpdateRequest,
)
from gm_shield.features.notes import service
from gm_shield.shared.database.sqlite import get_db

router = APIRouter()


@router.get(
    "",
    response_model=NoteListResponse,
    summary="List notes",
    description="Returns all notes ordered by last update timestamp.",
    responses={200: {"description": "Notes retrieved successfully."}},
)
def list_notes_endpoint(db: Session = Depends(get_db)) -> NoteListResponse:
    """Return all saved notes."""
    return NoteListResponse(items=service.list_notes(db))


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Creates a new markdown note with optional frontmatter and tags.",
    responses={201: {"description": "Note created successfully."}},
)
def create_note_endpoint(payload: NoteCreateRequest, db: Session = Depends(get_db)) -> NoteResponse:
    """Create and return a note."""
    return service.create_note(db, payload)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get note",
    description="Returns a single note by its identifier.",
    responses={200: {"description": "Note retrieved successfully."}, 404: {"description": "Note not found."}},
)
def get_note_endpoint(note_id: int, db: Session = Depends(get_db)) -> NoteResponse:
    """Fetch one note by ID."""
    return service.get_note(db, note_id)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update note",
    description="Replaces an existing note and updates its modification timestamp.",
    responses={200: {"description": "Note updated successfully."}, 404: {"description": "Note not found."}},
)
def update_note_endpoint(
    note_id: int,
    payload: NoteUpdateRequest,
    db: Session = Depends(get_db),
) -> NoteResponse:
    """Update and return a note."""
    return service.update_note(db, note_id, payload)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Deletes a note by identifier.",
    responses={204: {"description": "Note deleted successfully."}, 404: {"description": "Note not found."}},
)
def delete_note_endpoint(note_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a note and return an empty response."""
    service.delete_note(db, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
