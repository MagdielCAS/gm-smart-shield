"""
GM Smart Shield — FastAPI application entry point.

Wires together the application lifecycle, router registration, and optional telemetry.
All routes are grouped by feature slice and mounted under /api/v1.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from gm_shield.core.config import settings
from gm_shield.shared.database.sqlite import engine, Base
from gm_shield.features.health import routes as health_routes
from gm_shield.features.knowledge import router as knowledge_router_module
from gm_shield.core.telemetry import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    On startup: initialises SQLite tables and ensures ChromaDB directory exists.
    On shutdown: performs any necessary cleanup (currently a no-op).
    """
    # Startup: create all SQLAlchemy-mapped tables if they don't exist yet.
    # Replace with Alembic migrations once the schema stabilises.
    Base.metadata.create_all(bind=engine)
    print(f"SQLite database ready at {settings.SQLITE_URL}")
    print(f"ChromaDB persistence directory: {settings.CHROMA_PERSIST_DIRECTORY}")

    yield

    print("Shutting down GM Smart Shield API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "**GM Smart Shield** is a locally-hosted AI assistant for tabletop RPG Game Masters.\n\n"
        "It provides:\n"
        "- 📚 **Knowledge ingestion** — upload PDFs, Markdown, and text files to build a searchable knowledge base\n"
        "- 💬 **Q&A chat** — ask questions answered by your documents via RAG (Retrieval-Augmented Generation)\n"
        "- 📝 **Notes** — create and manage GM session notes with automatic tagging\n"
        "- 🎲 **Encounters** — generate encounter narratives powered by a local LLM\n"
        "- 🧾 **Character Sheets** — manage player character sheets derived from rulebook templates\n"
        "- 📖 **Quick References** — auto-generated reference cards extracted from source documents\n\n"
        "All inference runs **locally** via Ollama — no external cloud services required.\n\n"
        "> **Version:** 0.1.0 — Pre-Alpha"
    ),
    version="0.1.0",
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
    """Root endpoint — confirms the API is running."""
    return {"message": "Welcome to GM Smart Shield API"}


# ── Feature routers ─────────────────────────────────────────────────────────
# Each router is registered with a prefix that matches the API design in TECHNICAL.md.

app.include_router(
    health_routes.router,
    prefix=settings.API_V1_STR,
    tags=["Health"],
)

app.include_router(
    knowledge_router_module.router,
    prefix=f"{settings.API_V1_STR}/knowledge",
    tags=["Knowledge"],
)
