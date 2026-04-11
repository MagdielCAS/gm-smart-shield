from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from gm_shield.shared.database.sqlite import get_db
from gm_shield.features.sheets import service, schemas
from gm_shield.features.knowledge.models import CharacterSheetTemplate

router = APIRouter()


@router.get("", response_model=List[schemas.CharacterSheetResponse])
def read_sheets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List character sheets."""
    return service.get_character_sheets(db, skip=skip, limit=limit)


@router.post("", response_model=schemas.CharacterSheetResponse, status_code=201)
def create_sheet(sheet: schemas.CharacterSheetCreate, db: Session = Depends(get_db)):
    """Create a new character sheet."""
    return service.create_character_sheet(db=db, sheet_in=sheet)


@router.get("/templates", response_model=List[dict])
def list_templates(db: Session = Depends(get_db)):
    """List character sheet templates extracted from rulebooks."""
    templates = db.query(CharacterSheetTemplate).all()
    # Simple dict conversion, since we don't have a rigid Pydantic schema for templates yet
    return [
        {
            "id": t.id,
            "name": t.name,
            "system": t.system,
            "template_schema": t.template_schema,
            "source_id": t.source_id,
        }
        for t in templates
    ]


@router.get("/{sheet_id}", response_model=schemas.CharacterSheetResponse)
def read_sheet(sheet_id: str, db: Session = Depends(get_db)):
    """Get a character sheet."""
    sheet = service.get_character_sheet(db, sheet_id=sheet_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail="Sheet not found")
    return sheet


@router.put("/{sheet_id}", response_model=schemas.CharacterSheetResponse)
def update_sheet(
    sheet_id: str, sheet_in: schemas.CharacterSheetUpdate, db: Session = Depends(get_db)
):
    """Update a character sheet."""
    return service.update_character_sheet(db=db, sheet_id=sheet_id, sheet_in=sheet_in)


@router.delete("/{sheet_id}", status_code=204)
def delete_sheet(sheet_id: str, db: Session = Depends(get_db)):
    """Delete a character sheet."""
    success = service.delete_character_sheet(db=db, sheet_id=sheet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sheet not found")
    return


@router.get("/public/{sheet_id}", response_model=schemas.CharacterSheetResponse)
def read_public_sheet(sheet_id: str, db: Session = Depends(get_db)):
    """Publicly read a character sheet if `is_public` is true."""
    sheet = service.get_character_sheet(db, sheet_id=sheet_id)
    if sheet is None or not sheet.is_public:
        raise HTTPException(status_code=404, detail="Sheet not found")
    return sheet


