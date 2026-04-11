from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


class CharacterSheetCreate(BaseModel):
    template_id: int
    player_name: str = Field(..., min_length=1)
    character_name: str = Field(..., min_length=1)
    content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_public: bool = False


class CharacterSheetUpdate(BaseModel):
    player_name: Optional[str] = None
    character_name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class CharacterSheetResponse(BaseModel):
    id: str
    template_id: int
    player_name: str
    character_name: str
    content: Dict[str, Any]
    is_public: bool

    model_config = ConfigDict(from_attributes=True)
