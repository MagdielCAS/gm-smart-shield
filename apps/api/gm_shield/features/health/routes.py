"""
Health feature — detailed dependency health check router.

Exposes ``GET /api/v1/health/status`` which checks the three core dependencies:
- **SQLite** — executes a trivial ``SELECT 1`` query
- **ChromaDB** — calls the client heartbeat
- **Ollama** — fetches the model tag list and verifies all required models are present

Also exposes ``GET /api/v1/system/llm-health`` for a focused AI subsystem check.
"""

from typing import Dict, List

import httpx
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger
from gm_shield.shared.database.chroma import get_chroma_client
from gm_shield.shared.database.sqlite import get_db
from gm_shield.shared.llm import config as llm_config
from gm_shield.shared.llm.client import get_llm_client

logger = get_logger(__name__)
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
    chroma: bool = Field(..., description="``True`` if ChromaDB heartbeat succeeded.")
    ollama: bool = Field(..., description="``True`` if the Ollama server is reachable.")
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
            "description": "Health report returned. Inspect the response fields to determine "
            "whether individual services are healthy — the HTTP status code is always 200."
        }
    },
)
async def check_health_status(db: Session = Depends(get_db)):
    """
    Return the health status of all infrastructure dependencies.

    Checks are performed in parallel for:
    - **SQLite** — executes a trivial `SELECT 1` query.
    - **ChromaDB** — calls the client heartbeat.
    - **Ollama** — lists available models and cross-references them against the three
      required model names defined in settings (`OLLAMA_MODEL_GENERAL`,
      `OLLAMA_MODEL_STRUCTURED`, `OLLAMA_MODEL_CREATIVE`).

    The endpoint **always returns HTTP 200**. Consumers must inspect the individual
    boolean fields and the `errors` list to determine whether a service is unhealthy.
    """
    health = HealthStatus(database=False, chroma=False, ollama=False, ollama_models={})

    # Check SQLite connectivity
    try:
        db.execute(text("SELECT 1"))
        health.database = True
        logger.info("sqlite_ok")
    except Exception as e:
        logger.warning("sqlite_error", error=str(e))
        health.errors.append(f"SQLite error: {str(e)}")

    # Check ChromaDB connectivity
    try:
        chroma_client = get_chroma_client()
        chroma_client.heartbeat()
        health.chroma = True
        logger.info("chroma_ok")
    except Exception as e:
        logger.warning("chroma_error", error=str(e))
        health.errors.append(f"ChromaDB error: {str(e)}")

    # Check Ollama connectivity and required model availability
    required_models = [
        settings.OLLAMA_MODEL_GENERAL,
        settings.OLLAMA_MODEL_STRUCTURED,
        settings.OLLAMA_MODEL_CREATIVE,
    ]

    for model_name in required_models:
        health.ollama_models[model_name] = False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0
            )

            if response.status_code == 200:
                health.ollama = True
                data = response.json()
                available_models = [m.get("name", "") for m in data.get("models", [])]
                logger.info("ollama_ok", available_models=available_models)

                for required in required_models:
                    # Exact match first; fall back to prefix match
                    if required in available_models or any(
                        avail.startswith(required) for avail in available_models
                    ):
                        health.ollama_models[required] = True
                    else:
                        logger.warning("ollama_model_missing", model=required)
                        health.errors.append(f"Missing required model: {required}")
            else:
                logger.warning("ollama_bad_status", status_code=response.status_code)
                health.errors.append(f"Ollama returned status {response.status_code}")

    except httpx.RequestError as e:
        logger.warning("ollama_connection_failed", error=str(e))
        health.errors.append(f"Ollama connection failed: {str(e)}")
    except Exception as e:
        logger.warning("ollama_check_error", error=str(e))
        health.errors.append(f"Ollama check error: {str(e)}")

    return health


# ── LLM Health ───────────────────────────────────────────────────────────────


class LLMHealthResponse(BaseModel):
    """
    Simplified health status for the AI subsystem.
    Used by the frontend to show a 'ready' indicator.
    """

    status: str = Field(
        ..., description="Overall status: 'ready', 'pulling', or 'error'."
    )
    models: Dict[str, bool] = Field(..., description="Availability of required models.")


@router.get(
    "/api/v1/system/llm-health",
    response_model=LLMHealthResponse,
    tags=["System"],
    summary="Check AI subsystem health",
    description="Verifies that Ollama is reachable and all required models are pulled.",
)
async def check_llm_health():
    """
    Check if Ollama is running and all required models are pulled.
    Uses the internal OllamaClient for verification.
    """
    client = get_llm_client()
    required_models = list(
        {
            llm_config.MODEL_QUERY,
            llm_config.MODEL_REFERENCE_SMART,
            llm_config.MODEL_ENCOUNTER,
        }
    )

    models_status = {m: False for m in required_models}
    all_ready = True

    try:
        available = await client.list_models()
        available_names = [m["name"] for m in available]

        for req in required_models:
            # Check for exact or prefix match
            is_present = req in available_names or any(
                a.startswith(req) for a in available_names
            )
            models_status[req] = is_present
            if not is_present:
                all_ready = False

        return LLMHealthResponse(
            status="ready" if all_ready else "pulling",
            models=models_status,
        )
    except Exception as e:
        logger.error("llm_health_check_failed", error=str(e))
        # Return error status but preserve model list structure
        return LLMHealthResponse(status="error", models=models_status)
