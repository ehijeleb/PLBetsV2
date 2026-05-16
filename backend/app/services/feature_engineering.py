"""Roll engineered features off historical match data.

All features are computed using only matches *prior* to the target match, so
nothing leaks forward in time when we train/predict.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from app.services.data_loader import canon_team, load_all_history


# Public list — the model trains on these and they're echoed back in SHAP labels.
FEATURE_COLUMNS: list[str] = [
    # Home rolling-5 (at home)
    "home_wins_last5", "home_draws_last5", "home_losses_last5",
    "home_goals_scored_last5", "home_goals_conceded_last5", "home_clean_sheets_last5",
    # Away rolling-5 (away)
    "away_wins_last5", "away_draws_last5", "away_losses_last5",
    "away_goals_scored_last5", "away_goals_conceded_last5", "away_clean_sheets_last5",
    # Season context
    "home_points_per_game", "away_points_per_game",
    "home_goal_diff_pg", "away_goal_diff_pg",
    "home_position_proxy", "away_position_proxy",
    # H2H (last 10)
    "h2h_home_wins", "h2h_draws", "h2h_away_wins",
    "h2h_home_goals_avg", "h2h_away_goals_avg",
    # Referee
    "referee_home_win_rate", "referee_cards_per_game",
    # Match context
    "is_weekend", "kickoff_hour",
]

# Human-readable labels for SHAP output.
FEATURE_LABELS: dict[str, str] = {
    "home_wins_last5": "Home team — wins in last 5 home games",
    "home_draws_last5": "Home team — draws in last 5 home games",
    "home_losses_last5": "Home team — losses in last 5 home games",
    "home_goals_scored_last5": "Home team — goals scored (last 5 home)",
    "home_goals_conceded_last5": "Home team — goals conceded (last 5 home)",
    "home_clean_sheets_last5": "Home team — clean sheets (last 5 home)",
    "away_wins_last5": "Away team — wins in last 5 away games",
    "away_draws_last5": "Away team — draws in last 5 away games",
    "away_losses_last5": "Away team — losses in last 5 away games",
    "away_goals_scored_last5": "Away team — goals scored (last 5 away)",
    "away_goals_conceded_last5": "Away team — goals conceded (last 5 away)",
    "away_clean_sheets_last5": "Away team — clean sheets (last 5 away)",
    "home_points_per_game": "Home team — points per game this season",
    "away_points_per_game": "Away team — points per game this season",
    "home_goal_diff_pg": "Home team — goal difference per game (season)",
    "away_goal_diff_pg": "Away team — goal difference per game (season)",
    "home_position_proxy": "Home team — league standing (proxy)",
    "away_position_proxy": "Away team — league standing (proxy)",
    "h2h_home_wins": "Head-to-head — home wins (last 10)",
    "h2h_draws": "Head-to-head — draws (last 10)",
    "h2h_away_wins": "Head-to-head — away wins (last 10)",
    "h2h_home_goals_avg": "Head-to-head — avg home goals",
    "h2h_away_goals_avg": "Head-to-head — avg away goals",
    "referee_home_win_rate": "Referee — historical home win rate",
    "referee_cards_per_game": "Referee — average cards per game",
    "is_weekend": "Played on a weekend",
    "kickoff_hour": "Kick-off hour",
}


@dataclass
class FeatureContext:
    """Snapshot of the world that's needed to build features for a single match."""
    df: pd.DataFrame                       # all historical matches up to (excl.) the target


# ─── Helpers that work off a DataFrame snapshot ───────────────────────────────

def _last_n_for_team(df: pd.DataFrame, team: str, *, home: bool, n: int = 5) -> pd.DataFrame:
    col = "home" if home else "away"
    return df[df[col] == team].sort_values("date").tail(n)


def _team_rolling(df: pd.DataFrame, team: str, *, home: bool, n: int = 5) -> dict:
    games = _last_n_for_team(df, team, home=home, n=n)
    wins = draws = losses = gs = gc = cs = 0
    for _, r in games.iterrows():
        if home:
            gf, ga = int(r["fthg"]), int(r["ftag"])
            res = r["ftr"]
            if res == "H":
                wins += 1
            elif res == "D":
                draws += 1
            else:
                losses += 1
        else:
            gf, ga = int(r["ftag"]), int(r["fthg"])
            res = r["ftr"]
            if res == "A":
                wins += 1
            elif res == "D":
                draws += 1
            else:
                losses += 1
        gs += gf
        gc += ga
        if ga == 0:
            cs += 1
    return {
        "wins": wins, "draws": draws, "losses": losses,
        "goals_scored": gs, "goals_conceded": gc, "clean_sheets": cs,
    }


def _season_table(df: pd.DataFrame, season: str) -> pd.DataFrame:
    """Build a league-table snapshot from matches in `season` that exist in df."""
    season_df = df[df["season"] == season] if "season" in df.columns else df
    rows: dict[str, dict] = {}
    for _, r in season_df.iterrows():
        for side, team, gf, ga in (
            ("H", r["home"], r["fthg"], r["ftag"]),
            ("A", r["away"], r["ftag"], r["fthg"]),
        ):
            row = rows.setdefault(team, {"played": 0, "points": 0, "gf": 0, "ga": 0})
            row["played"] += 1
            row["gf"] += int(gf)
            row["ga"] += int(ga)
            if (side == "H" and r["ftr"] == "H") or (side == "A" and r["ftr"] == "A"):
                row["points"] += 3
            elif r["ftr"] == "D":
                row["points"] += 1
    tbl = pd.DataFrame.from_dict(rows, orient="index")
    if tbl.empty:
        return tbl
    tbl["gd"] = tbl["gf"] - tbl["ga"]
    tbl = tbl.sort_values(["points", "gd", "gf"], ascending=[False, False, False])
    tbl["position"] = range(1, len(tbl) + 1)
    return tbl


def _season_for_date(date: pd.Timestamp, history: pd.DataFrame) -> str:
    """Return the season label that owns `date`, e.g. '2024-25'.

    A season runs Aug→May, so dates in Jan–Jul belong to the season that ends that year.
    """
    y = date.year
    season_end = y if date.month <= 7 else y + 1
    label = f"{season_end - 1}-{str(season_end)[-2:]}"
    if "season" in history.columns and label in history["season"].unique():
        return label
    # Fall back to whatever season has the most rows nearest to this date.
    if "season" in history.columns and not history.empty:
        return history.iloc[-1]["season"]
    return label


def _season_context(df: pd.DataFrame, team: str, date: pd.Timestamp) -> dict:
    season = _season_for_date(date, df)
    season_df = df[(df["season"] == season) & (df["date"] < date)] if "season" in df.columns else df[df["date"] < date]
    tbl = _season_table(season_df, season)
    if tbl.empty or team not in tbl.index:
        return {"ppg": 1.0, "gd_pg": 0.0, "position_proxy": 10.5}
    row = tbl.loc[team]
    played = max(int(row["played"]), 1)
    return {
        "ppg": float(row["points"]) / played,
        "gd_pg": float(row["gd"]) / played,
        "position_proxy": float(row["position"]),
    }


def _h2h(df: pd.DataFrame, home: str, away: str, n: int = 10) -> dict:
    mask = ((df["home"] == home) & (df["away"] == away)) | ((df["home"] == away) & (df["away"] == home))
    games = df[mask].sort_values("date").tail(n)
    home_wins = draws = away_wins = 0
    home_goals = away_goals = 0.0
    for _, r in games.iterrows():
        if r["home"] == home:
            hg, ag = int(r["fthg"]), int(r["ftag"])
        else:
            hg, ag = int(r["ftag"]), int(r["fthg"])
        home_goals += hg
        away_goals += ag
        if hg > ag:
            home_wins += 1
        elif hg < ag:
            away_wins += 1
        else:
            draws += 1
    played = max(len(games), 1)
    return {
        "h2h_home_wins": home_wins,
        "h2h_draws": draws,
        "h2h_away_wins": away_wins,
        "h2h_home_goals_avg": home_goals / played if len(games) else 0.0,
        "h2h_away_goals_avg": away_goals / played if len(games) else 0.0,
    }


def _referee(df: pd.DataFrame, name: str | None) -> dict:
    if not name or "referee" not in df.columns:
        return {"referee_home_win_rate": 0.46, "referee_cards_per_game": 3.8}
    sub = df[df["referee"] == name]
    if sub.empty:
        return {"referee_home_win_rate": 0.46, "referee_cards_per_game": 3.8}
    home_win_rate = float((sub["ftr"] == "H").mean())
    cards_cols = [c for c in ("hy", "ay", "hr", "ar") if c in sub.columns]
    cards_per_game = float(sub[cards_cols].sum(axis=1).mean()) if cards_cols else 3.8
    return {"referee_home_win_rate": home_win_rate, "referee_cards_per_game": cards_per_game}


# ─── Public API ───────────────────────────────────────────────────────────────

def build_features_for_match(
    *,
    home_team: str,
    away_team: str,
    kickoff: pd.Timestamp | None = None,
    referee: str | None = None,
    history: pd.DataFrame | None = None,
) -> dict:
    """Produce a feature dict for a single match."""
    home_team = canon_team(home_team)
    away_team = canon_team(away_team)
    df = history if history is not None else load_all_history()
    if kickoff is None:
        kickoff = df["date"].max() + pd.Timedelta(days=1) if not df.empty else pd.Timestamp.utcnow()
    # Normalise to tz-naive — historical CSV dates are naive, pandas 3.0 forbids mixed comparisons.
    kickoff = pd.Timestamp(kickoff)
    if kickoff.tz is not None:
        kickoff = kickoff.tz_localize(None)
    df_prior = df[df["date"] < kickoff]

    home_form = _team_rolling(df_prior, home_team, home=True, n=5)
    away_form = _team_rolling(df_prior, away_team, home=False, n=5)
    home_ctx = _season_context(df_prior, home_team, kickoff)
    away_ctx = _season_context(df_prior, away_team, kickoff)
    h2h = _h2h(df_prior, home_team, away_team, n=10)
    ref = _referee(df_prior, referee)

    features = {
        "home_wins_last5": home_form["wins"],
        "home_draws_last5": home_form["draws"],
        "home_losses_last5": home_form["losses"],
        "home_goals_scored_last5": home_form["goals_scored"],
        "home_goals_conceded_last5": home_form["goals_conceded"],
        "home_clean_sheets_last5": home_form["clean_sheets"],
        "away_wins_last5": away_form["wins"],
        "away_draws_last5": away_form["draws"],
        "away_losses_last5": away_form["losses"],
        "away_goals_scored_last5": away_form["goals_scored"],
        "away_goals_conceded_last5": away_form["goals_conceded"],
        "away_clean_sheets_last5": away_form["clean_sheets"],
        "home_points_per_game": home_ctx["ppg"],
        "away_points_per_game": away_ctx["ppg"],
        "home_goal_diff_pg": home_ctx["gd_pg"],
        "away_goal_diff_pg": away_ctx["gd_pg"],
        "home_position_proxy": home_ctx["position_proxy"],
        "away_position_proxy": away_ctx["position_proxy"],
        **h2h,
        **ref,
        "is_weekend": int(kickoff.weekday() >= 5),
        "kickoff_hour": int(kickoff.hour),
    }
    return features


def build_training_matrix(history: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """Iterate every match in history (skipping the first season as warm-up) and
    build the (X, y) pair the ensemble trains on.
    """
    df = history if history is not None else load_all_history()
    if df.empty:
        raise RuntimeError("No historical data available — run ml/download_data.py first.")

    # Use ALL matches; rolling features will simply be zero-filled for the very early ones.
    rows: list[dict] = []
    targets: list[int] = []
    df = df.sort_values("date").reset_index(drop=True)

    # We expose a progress hook via prints (no tqdm dep). One row per match.
    n = len(df)
    last_pct = -1
    for i, r in df.iterrows():
        feats = build_features_for_match(
            home_team=r["home"],
            away_team=r["away"],
            kickoff=r["date"],
            referee=r.get("referee"),
            history=df.iloc[:i],   # strictly prior
        )
        rows.append(feats)
        targets.append(0 if r["ftr"] == "H" else (1 if r["ftr"] == "D" else 2))
        pct = (i * 100) // n
        if pct != last_pct and pct % 10 == 0:
            print(f"  feature engineering: {pct}% ({i}/{n})")
            last_pct = pct

    X = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    y = pd.Series(targets, name="outcome")
    return X, y
