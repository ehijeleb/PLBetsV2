"""Stats endpoints — form, H2H, league-table form heatmap, home-vs-away splits."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter

from app.services.data_loader import canon_team, load_all_history, all_teams as list_all_teams


router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/form/{team}")
async def team_form(team: str, last: int = 10) -> dict[str, Any]:
    df = load_all_history()
    if df.empty:
        return {"team": team, "matches": []}
    team = canon_team(team)
    sub = df[(df["home"] == team) | (df["away"] == team)].sort_values("date").tail(last)
    rows = []
    for _, r in sub.iterrows():
        if r["home"] == team:
            gf, ga, opp, venue = int(r["fthg"]), int(r["ftag"]), r["away"], "H"
            res = "W" if r["ftr"] == "H" else ("D" if r["ftr"] == "D" else "L")
        else:
            gf, ga, opp, venue = int(r["ftag"]), int(r["fthg"]), r["home"], "A"
            res = "W" if r["ftr"] == "A" else ("D" if r["ftr"] == "D" else "L")
        rows.append(
            {
                "date": r["date"].isoformat(),
                "opponent": opp,
                "venue": venue,
                "goals_for": gf,
                "goals_against": ga,
                "result": res,
            }
        )
    return {"team": team, "matches": rows}


@router.get("/h2h/{home}/{away}")
async def h2h(home: str, away: str, last: int = 10) -> dict[str, Any]:
    df = load_all_history()
    if df.empty:
        return {"home_team": home, "away_team": away, "matches": []}
    home_c, away_c = canon_team(home), canon_team(away)
    mask = ((df["home"] == home_c) & (df["away"] == away_c)) | ((df["home"] == away_c) & (df["away"] == home_c))
    sub = df[mask].sort_values("date").tail(last)
    rows = [
        {
            "date": r["date"].isoformat(),
            "home_team": r["home"],
            "away_team": r["away"],
            "home_goals": int(r["fthg"]),
            "away_goals": int(r["ftag"]),
        }
        for _, r in sub.iterrows()
    ]
    return {"home_team": home_c, "away_team": away_c, "matches": rows}


@router.get("/form-heatmap")
async def form_heatmap(last: int = 10) -> dict[str, Any]:
    """One row per team, listing the W/D/L for their most recent `last` matches."""
    df = load_all_history()
    if df.empty:
        return {"teams": []}
    out: list[dict[str, Any]] = []
    teams = list_all_teams()
    # Use only teams that played in the most recent season to keep this current.
    if "season" in df.columns:
        last_season = df.sort_values("date").iloc[-1]["season"]
        active = set(df[df["season"] == last_season]["home"]).union(df[df["season"] == last_season]["away"])
        teams = [t for t in teams if t in active]
    for team in teams:
        sub = df[(df["home"] == team) | (df["away"] == team)].sort_values("date").tail(last)
        results = []
        for _, r in sub.iterrows():
            if r["home"] == team:
                res = "W" if r["ftr"] == "H" else ("D" if r["ftr"] == "D" else "L")
            else:
                res = "W" if r["ftr"] == "A" else ("D" if r["ftr"] == "D" else "L")
            results.append(res)
        out.append({"team": team, "results": results})
    return {"teams": out}


@router.get("/home-vs-away")
async def home_vs_away() -> dict[str, Any]:
    """Per-team home win rate vs away win rate (current season if available)."""
    df = load_all_history()
    if df.empty:
        return {"teams": []}
    season_df = df
    if "season" in df.columns:
        last_season = df.sort_values("date").iloc[-1]["season"]
        season_df = df[df["season"] == last_season]
    home_stats = defaultdict(lambda: {"played": 0, "won": 0})
    away_stats = defaultdict(lambda: {"played": 0, "won": 0})
    for _, r in season_df.iterrows():
        home_stats[r["home"]]["played"] += 1
        away_stats[r["away"]]["played"] += 1
        if r["ftr"] == "H":
            home_stats[r["home"]]["won"] += 1
        elif r["ftr"] == "A":
            away_stats[r["away"]]["won"] += 1
    teams = sorted(set(home_stats).union(away_stats))
    out = []
    for t in teams:
        hp = home_stats[t]["played"] or 1
        ap = away_stats[t]["played"] or 1
        out.append(
            {
                "team": t,
                "home_win_rate": home_stats[t]["won"] / hp,
                "away_win_rate": away_stats[t]["won"] / ap,
                "home_played": home_stats[t]["played"],
                "away_played": away_stats[t]["played"],
            }
        )
    return {"teams": out}


@router.get("/teams")
async def teams_list() -> dict[str, Any]:
    return {"teams": list_all_teams()}


@router.get("/referees")
async def referees_list(min_matches: int = 10) -> dict[str, Any]:
    from app.services.data_loader import referees as _ref
    return {"referees": _ref(min_matches=min_matches)}
