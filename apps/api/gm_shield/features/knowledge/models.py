from pydantic import BaseModel
from typing import Optional

class KnowledgeSourceCreate(BaseModel):
    file_path: str
    description: Optional[str] = None

class KnowledgeSourceResponse(BaseModel):
    task_id: str
    status: str
    message: str
