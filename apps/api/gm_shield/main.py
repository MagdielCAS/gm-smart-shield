from contextlib import asynccontextmanager
from fastapi import FastAPI

from gm_shield.core.config import settings
from gm_shield.shared.database.sqlite import engine, Base
from gm_shield.features.health import routes as health_routes
from gm_shield.core.telemetry import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist (basic migration for now)
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {settings.SQLITE_URL}")
    print(f"ChromaDB initialized at {settings.CHROMA_PERSIST_DIRECTORY}")

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Setup telemetry (metrics) if enabled
setup_telemetry(app)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "Welcome to GM Smart Shield API"}


app.include_router(health_routes.router, tags=["Health"])

# Placeholder for feature routers
# app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
