"""Runtime configuration sourced from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CACHE_DATA_DIR = DATA_DIR / "cache"
MODELS_DIR = BACKEND_ROOT / "models_out"

for _d in (RAW_DATA_DIR, PROCESSED_DATA_DIR, CACHE_DATA_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    FOOTBALL_DATA_API_KEY: str = ""
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"
    DATABASE_URL: str = f"sqlite:///{(BACKEND_ROOT / 'plbets.db').as_posix()}"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Cache TTLs (seconds)
    FIXTURES_TTL: int = 6 * 60 * 60         # 6h
    STANDINGS_TTL: int = 12 * 60 * 60       # 12h
    TEAMS_TTL: int = 7 * 24 * 60 * 60       # 7d
    H2H_TTL: int = 24 * 60 * 60             # 24h

    SCHEDULER_REFRESH_HOURS: int = 6

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
