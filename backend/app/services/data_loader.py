"""Load and normalise the football-data.co.uk historical CSVs.

The CSVs use abbreviated team names (e.g. 'Man United'). We keep an alias map
so the same team is matched whether it comes in from the brief, the API, or
the user's autocomplete input.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.config import RAW_DATA_DIR


logger = logging.getLogger(__name__)

# CSV columns that are reliably present across recent seasons.
_KEEP_COLS = {
    "Date": "date",
    "HomeTeam": "home",
    "AwayTeam": "away",
    "FTHG": "fthg",     # full-time home goals
    "FTAG": "ftag",
    "FTR": "ftr",       # H / D / A
    "HS": "hs",         # home shots
    "AS": "as_",        # away shots (rename to avoid the Python keyword)
    "HST": "hst",
    "AST": "ast",
    "HC": "hc",
    "AC": "ac",
    "HY": "hy",
    "AY": "ay",
    "HR": "hr",
    "AR": "ar",
    "Referee": "referee",
}

# Canonical team-name aliasing. Keep canonical names lowercase for matching.
TEAM_ALIASES: dict[str, str] = {
    "manchester united": "Manchester United",
    "man united": "Manchester United",
    "man utd": "Manchester United",
    "manchester city": "Manchester City",
    "man city": "Manchester City",
    "newcastle united": "Newcastle United",
    "newcastle": "Newcastle United",
    "tottenham hotspur": "Tottenham",
    "tottenham": "Tottenham",
    "spurs": "Tottenham",
    "wolverhampton wanderers": "Wolves",
    "wolverhampton": "Wolves",
    "wolves": "Wolves",
    "leicester city": "Leicester",
    "leicester": "Leicester",
    "leeds united": "Leeds",
    "leeds": "Leeds",
    "norwich city": "Norwich",
    "norwich": "Norwich",
    "brighton & hove albion": "Brighton",
    "brighton and hove albion": "Brighton",
    "brighton": "Brighton",
    "afc bournemouth": "Bournemouth",
    "bournemouth": "Bournemouth",
    "west ham united": "West Ham",
    "west ham": "West Ham",
    "west bromwich albion": "West Brom",
    "west brom": "West Brom",
    "sheffield united": "Sheffield United",
    "sheffield utd": "Sheffield United",
    "nottingham forest": "Nott'm Forest",
    "nott'm forest": "Nott'm Forest",
    "luton town": "Luton",
    "luton": "Luton",
    "ipswich town": "Ipswich",
    "ipswich": "Ipswich",
    "burnley": "Burnley",
    "watford": "Watford",
    "fulham": "Fulham",
    "arsenal": "Arsenal",
    "aston villa": "Aston Villa",
    "brentford": "Brentford",
    "chelsea": "Chelsea",
    "crystal palace": "Crystal Palace",
    "everton": "Everton",
    "liverpool": "Liverpool",
    "southampton": "Southampton",
    "cardiff city": "Cardiff",
    "cardiff": "Cardiff",
    "huddersfield town": "Huddersfield",
    "huddersfield": "Huddersfield",
    "stoke city": "Stoke",
    "stoke": "Stoke",
    "swansea city": "Swansea",
    "swansea": "Swansea",
    "hull city": "Hull",
    "hull": "Hull",
    "middlesbrough": "Middlesbrough",
    "sunderland": "Sunderland",
    "qpr": "QPR",
    "queens park rangers": "QPR",
    "reading": "Reading",
}


def canon_team(name: str | None) -> str:
    if not name:
        return ""
    key = name.strip().lower()
    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key]
    # Fall back to title-case so unknown teams still get a sensible canonical.
    return name.strip()


def _read_one(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin-1", on_bad_lines="skip")
    present = [c for c in _KEEP_COLS if c in df.columns]
    if not present:
        logger.warning("data_loader: %s has none of the expected columns", path.name)
        return pd.DataFrame()
    df = df[present].rename(columns={c: _KEEP_COLS[c] for c in present})

    # Parse the date — football-data.co.uk uses DD/MM/YYYY (sometimes DD/MM/YY).
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date", "home", "away", "fthg", "ftag", "ftr"])
    df["fthg"] = df["fthg"].astype(int)
    df["ftag"] = df["ftag"].astype(int)
    df["home"] = df["home"].map(canon_team)
    df["away"] = df["away"].map(canon_team)
    df["season"] = path.stem.replace("E0_", "")
    return df


def list_available_csvs() -> list[Path]:
    return sorted(RAW_DATA_DIR.glob("E0_*.csv"))


@lru_cache(maxsize=1)
def load_all_history() -> pd.DataFrame:
    """Concatenate every CSV in data/raw/ into a single tidy DataFrame, sorted by date."""
    files = list_available_csvs()
    if not files:
        logger.warning("data_loader: no E0_*.csv files in %s — run ml/download_data.py", RAW_DATA_DIR)
        return pd.DataFrame(columns=["date", "home", "away", "fthg", "ftag", "ftr", "season"])
    frames = [_read_one(p) for p in files]
    df = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def reload_history() -> pd.DataFrame:
    load_all_history.cache_clear()
    return load_all_history()


def all_teams() -> list[str]:
    df = load_all_history()
    if df.empty:
        return []
    teams = sorted(set(df["home"]).union(df["away"]))
    return [t for t in teams if t]


def referees(min_matches: int = 10) -> list[str]:
    df = load_all_history()
    if df.empty or "referee" not in df.columns:
        return []
    counts = df["referee"].value_counts()
    return counts[counts >= min_matches].index.tolist()
