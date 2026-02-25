"""
Health feature — detailed dependency health check router.

Exposes ``GET /api/v1/health/status`` which checks the three core dependencies:
- **SQLite** — executes a trivial ``SELECT 1`` query
- **ChromaDB** — calls the client heartbeat
- **Ollama** — fetches the model tag list and verifies all required models are present

The endpoint always returns HTTP 200 with a structured payload so monitoring tools
can distinguish between partial and full degradation without relying on status codes.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, List
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

from gm_shield.core.config import settings
from gm_shield.shared.database.sqlite import get_db
from gm_shield.shared.database.chroma import get_chroma_client

router = APIRouter()


# ── Response schema ───────────────────────────────────────────────────────────


class HealthStatus(BaseModel):
    """
    Detailed health status for all downstream dependencies.

    Each boolean field is ``True`` only when the dependency responded correctly.
    The ``errors`` list accumulates human-readable error messages for any
    dependency that is unavailable or partially degraded.
    """

    database: bool = Field(
        ..., description="``True`` if SQLite is reachable and queryable."
    )
    chroma: bool = Field(
        ..., description="``True`` if ChromaDB heartbeat succeeded."
    )
    ollama: bool = Field(
        ..., description="``True`` if the Ollama server is reachable."
    )
    ollama_models: Dict[str, bool] = Field(
        ...,
        description=(
            "Per-model availability map. Keys are the required model identifiers "
            "(e.g. ``llama3.2:3b``); values are ``True`` when the model is pulled "
            "and ready in Ollama."
        ),
    )
    errors: List[str] = Field(
        default=[],
        description="List of error messages for any failed dependency check.",
    )


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.get(
    "/health/status",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Detailed dependency health check",
    description=(
        "Checks the three core dependencies of GM Smart Shield and reports their status:\n\n"
        "| Dependency | Check performed |\n"
        "|---|---|\n"
        "| **SQLite** | Executes `SELECT 1` |\n"
        "| **ChromaDB** | Calls client heartbeat |\n"
        "| **Ollama** | Fetches model list via `/api/tags` and verifies required models |\n\n"
        "Always returns **HTTP 200** — inspect the response body fields to determine "
        "whether individual dependencies are healthy.\n\n"
        "For a lightweight liveness probe, use `GET /health` instead."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Health check completed. Inspect response fields for individual dependency status."
        }
    },
)
async def check_health_status(db: Session = Depends(get_db)) -> HealthStatus:
    """
    Run a full dependency health check and return the aggregated results.

    Checks are performed in order: SQLite → ChromaDB → Ollama + required models.
    Failures are non-fatal — all checks always run and their results are collected
    into the returned ``HealthStatus`` payload.
    """
    health = HealthStatus(
        database=False,
        chroma=False,
        ollama=False,
        ollama_models={},
    )

    # ── 1. SQLite ─────────────────────────────────────────────────────────────
    try:
        db.execute(text("SELECT 1"))
        health.database = True
    except Exception as e:
        health.errors.append(f"SQLite error: {e}")

    # ── 2. ChromaDB ───────────────────────────────────────────────────────────
    try:
        chroma_client = get_chroma_client()
        chroma_client.heartbeat()
        health.chroma = True
    except Exception as e:
        health.errors.append(f"ChromaDB error: {e}")

    # ── 3. Ollama + required model availability ───────────────────────────────
    required_models = [
        settings.OLLAMA_MODEL_GENERAL,
        settings.OLLAMA_MODEL_STRUCTURED,
        settings.OLLAMA_MODEL_CREATIVE,
    ]

    # Initialise all models as unavailable before querying
    for model_name in required_models:
        health.ollama_models[model_name] = False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0,
            )

            if response.status_code == 200:
                health.ollama = True
                data = response.json()
                available_models = [m.get("name", "") for m in data.get("models", [])]

                for required in required_models:
                    # Accept both exact matches (e.g. "llama3.2:3b") and prefix matches
                    # (e.g. "llama3.2:3b" matches "llama3.2:3b-instruct" in some registries).
                    if required in available_models or any(
                        avail.startswith(required) for avail in available_models
                    ):
                        health.ollama_models[required] = True
                    else:
                        health.errors.append(f"Missing required model: {required}")
            else:
                health.errors.append(
                    f"Ollama returned unexpected status: {response.status_code}"
                )

    except httpx.RequestError as e:
        health.errors.append(f"Ollama connection failed: {e}")
    except Exception as e:
        health.errors.append(f"Ollama check error: {e}")

    return health
