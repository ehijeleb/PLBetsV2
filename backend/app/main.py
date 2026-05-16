"""FastAPI entry point. Boots the app, wires routers, schedules background refresh."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.routers import fixtures, history, predict, stats
from app.services.football_api import get_football_client


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("plbets")

settings = get_settings()
scheduler = AsyncIOScheduler()


async def _refresh_cache() -> None:
    """Pre-warm cache for the upcoming-fixtures + standings endpoints."""
    try:
        client = await get_football_client()
        await client.upcoming_fixtures(limit=20)
        await client.standings()
        logger.info("Background refresh complete.")
    except Exception:
        logger.exception("Background refresh failed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialised.")
    scheduler.add_job(_refresh_cache, "interval", hours=settings.SCHEDULER_REFRESH_HOURS, id="refresh_cache")
    scheduler.start()
    logger.info("Scheduler started (refresh every %sh).", settings.SCHEDULER_REFRESH_HOURS)
    # Fire one warm-up pass on boot.
    try:
        await _refresh_cache()
    except Exception:
        pass
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="PLBets v2 API",
    description="Premier League intelligence dashboard — fixtures, predictions, stats, and history.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fixtures.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(stats.router)


@app.get("/")
async def root() -> dict:
    return {
        "service": "PLBets v2",
        "docs": "/docs",
        "endpoints": [
            "GET  /api/fixtures/upcoming",
            "GET  /api/fixtures/{id}",
            "GET  /api/teams",
            "GET  /api/standings",
            "POST /api/predict",
            "GET  /api/predict/history",
            "GET  /api/stats/form/{team}",
            "GET  /api/stats/h2h/{home}/{away}",
            "GET  /api/stats/form-heatmap",
            "GET  /api/stats/home-vs-away",
            "GET  /api/stats/teams",
            "GET  /api/stats/referees",
        ],
    }


@app.get("/health")
async def health() -> dict:
    from app.services.data_loader import list_available_csvs
    from app.services.model import MODEL_PATH
    return {
        "status": "ok",
        "history_csvs": [p.name for p in list_available_csvs()],
        "model_trained": MODEL_PATH.exists(),
        "football_data_key_set": bool(settings.FOOTBALL_DATA_API_KEY),
    }
