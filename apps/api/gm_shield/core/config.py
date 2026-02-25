"""
Application configuration via Pydantic Settings.

All settings can be overridden through environment variables or a ``.env`` file
placed in the working directory. Pydantic Settings automatically maps uppercase
env var names to the corresponding fields.

Example ``.env`` file::

    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL_CREATIVE=gemma3:12b-it-qat
    ENABLE_METRICS=true
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

# Resolve directory paths relative to this file so the application works
# regardless of the working directory from which uvicorn is launched.
_CURRENT_FILE = Path(__file__).parent.resolve()  # → apps/api/gm_shield/core/
_API_ROOT = _CURRENT_FILE.parent.parent  # → apps/api/
_REPO_ROOT = _API_ROOT.parent.parent  # → gm-smart-shield/ (monorepo root)
_DATA_DIR = _REPO_ROOT / "data"  # → gm-smart-shield/data/


class Settings(BaseSettings):
    """
    Central configuration object for GM Smart Shield API.

    Loaded once at import time from environment variables / ``.env`` file.
    Access the singleton via ``from gm_shield.core.config import settings``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Silently ignore env vars that don't map to a defined field
        extra="ignore",
    )

    # ── API ──────────────────────────────────────────────────────────────────
    API_V1_STR: str = "/api/v1"
    """URL prefix for all v1 routes (e.g. ``/api/v1/knowledge``)."""

    PROJECT_NAME: str = "GM Smart Shield"
    """Displayed as the API title in the Swagger / ReDoc UI."""

    # ── Databases ─────────────────────────────────────────────────────────────
    SQLITE_URL: str = f"sqlite:///{_DATA_DIR}/db/gm_shield.db"
    """SQLAlchemy connection string for the local SQLite database."""

    CHROMA_PERSIST_DIRECTORY: str = str(_DATA_DIR / "chroma")
    """Directory where ChromaDB stores its persistent vector collections."""

    # ── Background worker ─────────────────────────────────────────────────────
    WORKER_TYPE: str = "memory"
    """
    Task queue backend. Options:
    - ``memory`` — in-process asyncio queue (default, suitable for development)
    - ``redis`` — Redis-backed queue (planned for production)
    """

    # ── Telemetry ──────────────────────────────────────────────────────────────
    ENABLE_METRICS: bool = False
    """
    When ``True``, enables OpenTelemetry instrumentation and exposes a
    Prometheus-compatible ``/metrics`` endpoint.
    """

    # ── Ollama LLM runtime ────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    """Base URL of the local Ollama server."""

    OLLAMA_MODEL_GENERAL: str = "llama3.2:3b"
    """Model used for general Q&A and tagging tasks (fast, low memory)."""

    OLLAMA_MODEL_STRUCTURED: str = "granite4:latest"
    """Model used for structured generation and reference extraction."""

    OLLAMA_MODEL_CREATIVE: str = "gemma3:12b-it-qat"
    """Model used for creative tasks such as encounter generation (slower, higher quality)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure local data directories exist before the application tries to open them.
        os.makedirs(
            os.path.dirname(self.SQLITE_URL.replace("sqlite:///", "")),
            exist_ok=True,
        )
        os.makedirs(self.CHROMA_PERSIST_DIRECTORY, exist_ok=True)


settings = Settings()
