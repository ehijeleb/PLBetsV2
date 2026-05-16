"""Fixtures / teams / standings endpoints."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.football_api import get_football_client


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["fixtures"])


def _team_from_api(t: dict | None) -> dict:
    if not t:
        return {"id": 0, "name": "Unknown", "short_name": None, "tla": None, "crest": None}
    return {
        "id": t.get("id", 0),
        "name": t.get("name", "Unknown"),
        "short_name": t.get("shortName"),
        "tla": t.get("tla"),
        "crest": t.get("crest"),
    }


def _fixture_from_api(m: dict) -> dict:
    score = (m.get("score") or {}).get("fullTime") or {}
    return {
        "id": m.get("id", 0),
        "matchday": m.get("matchday"),
        "status": m.get("status", "SCHEDULED"),
        "utc_date": m.get("utcDate") or datetime.now(timezone.utc).isoformat(),
        "home_team": _team_from_api(m.get("homeTeam")),
        "away_team": _team_from_api(m.get("awayTeam")),
        "competition": ((m.get("competition") or {}).get("name") or "Premier League"),
        "venue": m.get("venue"),
        "home_goals": score.get("home"),
        "away_goals": score.get("away"),
    }


@router.get("/fixtures/upcoming")
async def upcoming(limit: int = 10) -> dict[str, Any]:
    client = await get_football_client()
    matches = await client.upcoming_fixtures(limit=limit)
    return {"fixtures": [_fixture_from_api(m) for m in matches], "source": "football-data.org"}


@router.get("/fixtures/{fixture_id}")
async def fixture(fixture_id: int) -> dict[str, Any]:
    client = await get_football_client()
    m = await client.fixture(fixture_id)
    if not m:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return _fixture_from_api(m)


@router.get("/teams")
async def teams() -> dict[str, Any]:
    client = await get_football_client()
    raw = await client.teams()
    return {"teams": [_team_from_api(t) for t in raw]}


@router.get("/standings")
async def standings() -> dict[str, Any]:
    client = await get_football_client()
    data = await client.standings()
    if not data:
        return {"season": None, "rows": []}
    season = ((data.get("season") or {}).get("startDate") or "").split("-")[0]
    table_block = next((s for s in (data.get("standings") or []) if s.get("type") == "TOTAL"), None)
    rows = []
    for row in (table_block or {}).get("table", []) if table_block else []:
        team = _team_from_api(row.get("team"))
        rows.append(
            {
                "position": row.get("position", 0),
                "team": team,
                "played": row.get("playedGames", 0),
                "won": row.get("won", 0),
                "draw": row.get("draw", 0),
                "lost": row.get("lost", 0),
                "points": row.get("points", 0),
                "goals_for": row.get("goalsFor", 0),
                "goals_against": row.get("goalsAgainst", 0),
                "goal_difference": row.get("goalDifference", 0),
                "form": row.get("form"),
            }
        )
    return {"season": season, "rows": rows}
