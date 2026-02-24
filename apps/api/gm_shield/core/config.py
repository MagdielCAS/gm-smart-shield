from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import DirectoryPath
import os
from pathlib import Path

# Get the directory of the current file
# This is usually apps/api/gm_shield/core
CURRENT_DIR = Path(__file__).parent.resolve()

# Root of the API project (apps/api)
API_ROOT = CURRENT_DIR.parent.parent

# Data directory (relative to the repo root, which is usually two levels up from apps/api)
# The user wants "data/db" and "data/chroma" at the repo root level (or relative to API root, it doesn't matter much as long as it is consistent)
# Let's assume repo root is 3 levels up from apps/api/gm_shield/core
REPO_ROOT = API_ROOT.parent.parent
DATA_DIR = REPO_ROOT / "data"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GM Smart Shield"

    # Database
    SQLITE_URL: str = f"sqlite:///{DATA_DIR}/db/gm_shield.db"
    CHROMA_PERSIST_DIRECTORY: str = str(DATA_DIR / "chroma")

    # Worker
    WORKER_TYPE: str = "memory"  # 'memory' or 'redis' (future)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directories exist
        os.makedirs(os.path.dirname(self.SQLITE_URL.replace("sqlite:///", "")), exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIRECTORY, exist_ok=True)


settings = Settings()
