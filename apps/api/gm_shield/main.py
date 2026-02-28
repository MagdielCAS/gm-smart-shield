"""
GM Smart Shield — FastAPI application entry point.

Wires together the application lifecycle, router registration, and optional telemetry.
All routes are grouped by feature slice and mounted under /api/v1.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from gm_shield.core.config import settings
from gm_shield.core.logging import configure_logging, get_logger
from gm_shield.shared.database.sqlite import engine, Base
from gm_shield.features.chat import routes as chat_routes
from gm_shield.features.health import routes as health_routes
from gm_shield.features.knowledge import router as knowledge_router_module
from gm_shield.features.notes import routes as notes_routes
from gm_shield.features.encounters import routes as encounter_routes
from gm_shield.features.mcp import routes as mcp_routes
from gm_shield.core.telemetry import setup_telemetry

# ── Logging ───────────────────────────────────────────────────────────────────
# Configure structlog once at import time so every module that obtains a logger
# via get_logger(__name__) shares the same processor chain.
configure_logging()
logger = get_logger(__name__)

_DESCRIPTION = """
**GM Smart Shield** is a locally-hosted AI assistant for tabletop Game Masters.

## Features (v0.1)

- **Knowledge Base** — ingest PDF, Markdown, text, and CSV files into a vector store for semantic search.
- **Health** — check the status of all infrastructure dependencies (SQLite, ChromaDB, Ollama).
- **Chat** — RAG-based Q&A with the knowledge base.

## Local-first design

All inference and storage runs on your machine. No external cloud services are required
for core functionality.
"""

_TAGS_METADATA = [
    {
        "name": "Knowledge",
        "description": "Upload and manage knowledge sources. "
        "Files are processed asynchronously: text is extracted, chunked, embedded, "
        "and stored in ChromaDB.",
    },
    {
        "name": "Health",
        "description": "Infrastructure health checks for SQLite, ChromaDB, and Ollama.",
    },
    {
        "name": "System",
        "description": "System-level status and configuration checks.",
    },
    {
        "name": "Chat",
        "description": "Query the AI agent for RAG-based answers.",
    },
    {
        "name": "Notes",
        "description": "Manage GM notes with auto-tagging capabilities.",
    },
    {
        "name": "Encounters",
        "description": "Generate tactical encounters and NPC stat blocks.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manage application startup and shutdown events.

    On startup: initialises SQLite tables and ensures ChromaDB directory exists.
    On shutdown: performs any necessary cleanup (currently a no-op).
    """
    Base.metadata.create_all(bind=engine)
    logger.info("database_initialized", url=settings.SQLITE_URL)
    logger.info("chroma_initialized", path=settings.CHROMA_PERSIST_DIRECTORY)

    yield

    logger.info("shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=_DESCRIPTION,
    contact={
        "name": "GM Smart Shield",
        "url": "https://github.com/magdielcampelo/gm-smart-shield",
    },
    license_info={"name": "MIT"},
    openapi_tags=_TAGS_METADATA,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Setup optional OpenTelemetry + Prometheus metrics (controlled by ENABLE_METRICS env var)
setup_telemetry(app)


@app.get(
    "/health",
    summary="Simple liveness probe",
    description="Returns a minimal `{status, version}` payload. Use `/api/v1/health/status` for a full dependency check.",
    tags=["Health"],
    include_in_schema=True,
)
async def health_check():
    """
    Lightweight liveness check — suitable for load balancers and container orchestrators.

    Returns the fixed application version and a static `"ok"` status.
    Does **not** verify downstream dependencies (database, ChromaDB, Ollama).
    Use `GET /api/v1/health/status` for a full dependency health report.
    """
    return {"status": "ok", "version": "0.1.0"}


@app.get(
    "/",
    summary="API root",
    description="Returns a welcome message confirming the API is reachable.",
    tags=["General"],
    include_in_schema=True,
)
async def root():
    """API root — redirects clients to the interactive docs."""
    return {
        "message": "Welcome to GM Smart Shield API",
        "docs": f"{settings.API_V1_STR}/docs",
    }


# ── Feature routers ─────────────────────────────────────────────────────────
# Each router is registered with a prefix that matches the API design in TECHNICAL.md.

app.include_router(
    health_routes.router,
    tags=["Health"],
)

app.include_router(
    knowledge_router_module.router,
    prefix=f"{settings.API_V1_STR}/knowledge",
    tags=["Knowledge"],
)

app.include_router(
    chat_routes.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["Chat"],
)

app.include_router(
    notes_routes.router,
    prefix=f"{settings.API_V1_STR}/notes",
    tags=["Notes"],
)

app.include_router(
    encounter_routes.router,
    prefix=f"{settings.API_V1_STR}/encounters",
    tags=["Encounters"],
)

app.include_router(
    mcp_routes.router,
    prefix=f"{settings.API_V1_STR}/mcp",
    tags=["MCP"],
)
