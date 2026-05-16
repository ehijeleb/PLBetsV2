"""Async client for football-data.org v4 with on-disk JSON caching.

All public methods return cleanly-shaped dicts/lists that the routers can map
straight onto Pydantic schemas. When the API key is missing or the upstream
call fails, the client falls back to whatever is already in the on-disk cache
so the app remains usable in offline / demo mode.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

import httpx

from app.config import CACHE_DATA_DIR, get_settings


logger = logging.getLogger(__name__)

PL_COMPETITION_CODE = "PL"  # Premier League


class FootballAPIError(RuntimeError):
    pass


class _Cache:
    """Tiny TTL-aware JSON cache on disk."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace("?", "_").replace("=", "_").replace("&", "_")
        return self.root / f"{safe}.json"

    def read(self, key: str, ttl: int) -> Optional[Any]:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if (time.time() - payload.get("_ts", 0)) > ttl:
            return None
        return payload.get("data")

    def read_stale(self, key: str) -> Optional[Any]:
        """Read regardless of TTL (used as offline fallback)."""
        p = self._path(key)
        if not p.exists():
            return None
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload.get("data")

    def write(self, key: str, data: Any) -> None:
        p = self._path(key)
        p.write_text(json.dumps({"_ts": time.time(), "data": data}), encoding="utf-8")


class FootballAPIClient:
    def __init__(self) -> None:
        s = get_settings()
        self.base_url = s.FOOTBALL_DATA_BASE_URL.rstrip("/")
        self.api_key = s.FOOTBALL_DATA_API_KEY
        self.cache = _Cache(CACHE_DATA_DIR)
        self.fixtures_ttl = s.FIXTURES_TTL
        self.standings_ttl = s.STANDINGS_TTL
        self.teams_ttl = s.TEAMS_TTL
        self.h2h_ttl = s.H2H_TTL

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    async def _get(self, path: str, *, ttl: int, params: dict | None = None) -> Any:
        cache_key = path + ("?" + "&".join(f"{k}={v}" for k, v in (params or {}).items()) if params else "")
        cached = self.cache.read(cache_key, ttl)
        if cached is not None:
            return cached

        if not self.has_key:
            # No key — return whatever stale data we have, otherwise empty.
            stale = self.cache.read_stale(cache_key)
            if stale is not None:
                return stale
            logger.info("football-data: no API key and no cache for %s", cache_key)
            return None

        url = f"{self.base_url}{path}"
        headers = {"X-Auth-Token": self.api_key}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 429:
                # Rate limited — fall back to stale cache.
                logger.warning("football-data: 429 rate limited for %s", url)
                return self.cache.read_stale(cache_key)
            resp.raise_for_status()
            data = resp.json()
            self.cache.write(cache_key, data)
            return data
        except Exception as exc:  # network or HTTP error — fall back if possible
            logger.warning("football-data: request failed for %s: %s", url, exc)
            return self.cache.read_stale(cache_key)

    # ── Public methods ────────────────────────────────────────────────────────

    async def upcoming_fixtures(self, limit: int = 10) -> list[dict]:
        data = await self._get(
            f"/competitions/{PL_COMPETITION_CODE}/matches",
            ttl=self.fixtures_ttl,
            params={"status": "SCHEDULED,TIMED"},
        )
        matches = (data or {}).get("matches", []) if data else []
        return matches[:limit]

    async def all_matches_in_matchday(self, matchday: int) -> list[dict]:
        data = await self._get(
            f"/competitions/{PL_COMPETITION_CODE}/matches",
            ttl=self.fixtures_ttl,
            params={"matchday": matchday},
        )
        return (data or {}).get("matches", []) if data else []

    async def teams(self) -> list[dict]:
        data = await self._get(f"/competitions/{PL_COMPETITION_CODE}/teams", ttl=self.teams_ttl)
        return (data or {}).get("teams", []) if data else []

    async def standings(self) -> dict:
        data = await self._get(f"/competitions/{PL_COMPETITION_CODE}/standings", ttl=self.standings_ttl)
        return data or {}

    async def fixture(self, fixture_id: int) -> Optional[dict]:
        data = await self._get(f"/matches/{fixture_id}", ttl=self.fixtures_ttl)
        return (data or {}).get("match") if data else None

    async def team_matches(self, team_id: int, limit: int = 10, status: str = "FINISHED") -> list[dict]:
        data = await self._get(
            f"/teams/{team_id}/matches",
            ttl=self.h2h_ttl,
            params={"status": status, "limit": limit},
        )
        return (data or {}).get("matches", [])[:limit] if data else []

    async def head_to_head(self, fixture_id: int, limit: int = 10) -> dict:
        data = await self._get(
            f"/matches/{fixture_id}/head2head",
            ttl=self.h2h_ttl,
            params={"limit": limit},
        )
        return data or {}

    async def scorers(self, limit: int = 10) -> list[dict]:
        data = await self._get(
            f"/competitions/{PL_COMPETITION_CODE}/scorers",
            ttl=self.standings_ttl,
            params={"limit": limit},
        )
        return (data or {}).get("scorers", []) if data else []


# Singleton — small footprint, safe to share across requests.
_client: Optional[FootballAPIClient] = None
_client_lock = asyncio.Lock()


async def get_football_client() -> FootballAPIClient:
    global _client
    if _client is None:
        async with _client_lock:
            if _client is None:
                _client = FootballAPIClient()
    return _client
