from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Dict, List
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

from gm_shield.core.config import settings
from gm_shield.shared.database.sqlite import get_db
from gm_shield.shared.database.chroma import get_chroma_client

router = APIRouter()


class HealthStatus(BaseModel):
    database: bool
    chroma: bool
    ollama: bool
    ollama_models: Dict[str, bool]
    errors: List[str] = []


@router.get(
    "/health/status", response_model=HealthStatus, status_code=status.HTTP_200_OK
)
async def check_health_status(db: Session = Depends(get_db)):
    """
    Detailed health check for database, ChromaDB, and Ollama services.
    """
    health = HealthStatus(database=False, chroma=False, ollama=False, ollama_models={})

    # 1. Check SQLite
    try:
        db.execute(text("SELECT 1"))
        health.database = True
    except Exception as e:
        health.errors.append(f"SQLite error: {str(e)}")

    # 2. Check ChromaDB
    try:
        # Client creation is fast, heartbeat checks if server is up (or file is accessible)
        chroma_client = get_chroma_client()
        chroma_client.heartbeat()
        health.chroma = True
    except Exception as e:
        health.errors.append(f"ChromaDB error: {str(e)}")

    # 3. Check Ollama & Models
    required_models = [
        settings.OLLAMA_MODEL_GENERAL,
        settings.OLLAMA_MODEL_STRUCTURED,
        settings.OLLAMA_MODEL_CREATIVE,
    ]

    # Initialize all models as not found
    for model_name in required_models:
        health.ollama_models[model_name] = False

    try:
        async with httpx.AsyncClient() as client:
            # Check connection by listing tags
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0
            )

            if response.status_code == 200:
                health.ollama = True
                data = response.json()
                available_models = [m.get("name", "") for m in data.get("models", [])]

                # Check required models
                for required in required_models:
                    # Match logic: exact match or "required:latest" matches "required"
                    # But typically "llama3.2:3b" matches "llama3.2:3b"
                    if required in available_models:
                        health.ollama_models[required] = True
                    # Also handle "latest" tag implicit behavior if needed,
                    # but explicit is better.
                    # Or verify if `required` is a substring of available (e.g. library/tag)
                    elif any(avail.startswith(required) for avail in available_models):
                        health.ollama_models[required] = True
                    else:
                        health.errors.append(f"Missing required model: {required}")
            else:
                health.errors.append(f"Ollama returned status {response.status_code}")

    except httpx.RequestError as e:
        health.errors.append(f"Ollama connection failed: {str(e)}")
    except Exception as e:
        health.errors.append(f"Ollama check error: {str(e)}")

    # If any check failed, we might want to return 503, but the requirement was just "checks connections".
    # We return 200 with the detailed status.
    # If the user wants to fail the request on error, they can check the fields.

    return health
