import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from gm_shield.features.sheets.models import CharacterSheet
from gm_shield.features.sheets.schemas import CharacterSheetCreate, CharacterSheetUpdate
from gm_shield.features.knowledge.models import CharacterSheetTemplate


def get_character_sheet(db: Session, sheet_id: str) -> Optional[CharacterSheet]:
    return db.query(CharacterSheet).filter(CharacterSheet.id == sheet_id).first()


def get_character_sheets(
    db: Session, skip: int = 0, limit: int = 100
) -> List[CharacterSheet]:
    return db.query(CharacterSheet).offset(skip).limit(limit).all()


def create_character_sheet(
    db: Session, sheet_in: CharacterSheetCreate
) -> CharacterSheet:
    template = (
        db.query(CharacterSheetTemplate)
        .filter(CharacterSheetTemplate.id == sheet_in.template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=400, detail="Sheet template not found")

    new_id = str(uuid.uuid4())
    db_sheet = CharacterSheet(
        id=new_id,
        template_id=sheet_in.template_id,
        player_name=sheet_in.player_name,
        character_name=sheet_in.character_name,
        content=sheet_in.content or {},
        is_public=sheet_in.is_public,
    )
    db.add(db_sheet)
    db.commit()
    db.refresh(db_sheet)
    return db_sheet


def update_character_sheet(
    db: Session, sheet_id: str, sheet_in: CharacterSheetUpdate
) -> CharacterSheet:
    db_sheet = get_character_sheet(db, sheet_id)
    if not db_sheet:
        raise HTTPException(status_code=404, detail="Character sheet not found")

    update_data = sheet_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sheet, key, value)

    db.commit()
    db.refresh(db_sheet)
    return db_sheet


def delete_character_sheet(db: Session, sheet_id: str) -> bool:
    db_sheet = get_character_sheet(db, sheet_id)
    if not db_sheet:
        return False

    db.delete(db_sheet)
    db.commit()
    return True
