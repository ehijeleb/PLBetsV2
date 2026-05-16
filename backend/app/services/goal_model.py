"""Poisson goal model — expected goals + derived markets (BTTS, Over/Under).

The classic Dixon-Coles-lite parameterisation:
    log(λ_home) = μ + α_home + β_away + γ        (home advantage)
    log(λ_away) = μ + α_away + β_home

Fit by Poisson regression on every team-as-home and team-as-away appearance
over the history we have on disk.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from scipy.stats import poisson

from app.config import MODELS_DIR
from app.services.data_loader import canon_team, load_all_history

logger = logging.getLogger(__name__)

GOAL_MODEL_PATH = MODELS_DIR / "goal_model.pkl"
MAX_GOALS = 8  # cap for scoreline-grid probability calcs


@dataclass
class PoissonGoalModel:
    teams: list[str] = field(default_factory=list)
    attack: dict[str, float] = field(default_factory=dict)
    defence: dict[str, float] = field(default_factory=dict)
    intercept: float = 0.0
    home_advantage: float = 0.25
    avg_home_goals: float = 1.50
    avg_away_goals: float = 1.15

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "PoissonGoalModel":
        from sklearn.linear_model import PoissonRegressor

        df = df.dropna(subset=["fthg", "ftag", "home", "away"]).copy()
        if df.empty:
            raise RuntimeError("No data to fit goal model on.")

        # Long-form: one row per (team, opponent, venue, goals).
        rows = []
        for _, r in df.iterrows():
            rows.append({"team": r["home"], "opp": r["away"], "is_home": 1, "goals": int(r["fthg"])})
            rows.append({"team": r["away"], "opp": r["home"], "is_home": 0, "goals": int(r["ftag"])})
        long = pd.DataFrame(rows)

        # One-hot teams as attackers and defenders. Drop one level to avoid collinearity.
        teams = sorted(set(long["team"]).union(long["opp"]))
        self.teams = teams
        att = pd.get_dummies(long["team"], prefix="att").astype(float)
        defn = pd.get_dummies(long["opp"], prefix="def").astype(float)
        # Drop a reference team for each design block (the model is still rank-deficient
        # otherwise — PoissonRegressor with α>0 would actually handle it, but cleanly
        # dropping keeps coefficients interpretable).
        ref_team = teams[0]
        att = att.drop(columns=[f"att_{ref_team}"], errors="ignore")
        defn = defn.drop(columns=[f"def_{ref_team}"], errors="ignore")
        X = pd.concat([att, defn, long[["is_home"]].astype(float)], axis=1)
        y = long["goals"].astype(int).values

        model = PoissonRegressor(alpha=1e-4, max_iter=400)
        model.fit(X, y)

        self.intercept = float(model.intercept_)
        self.attack = {ref_team: 0.0}
        self.defence = {ref_team: 0.0}
        for name, coef in zip(X.columns, model.coef_):
            if name.startswith("att_"):
                self.attack[name[4:]] = float(coef)
            elif name.startswith("def_"):
                self.defence[name[4:]] = float(coef)
            elif name == "is_home":
                self.home_advantage = float(coef)

        self.avg_home_goals = float(df["fthg"].mean())
        self.avg_away_goals = float(df["ftag"].mean())
        return self

    # ── Prediction ────────────────────────────────────────────────────────────

    def _team_lookup(self, team: str, table: dict[str, float], default: float = 0.0) -> float:
        if team in table:
            return table[team]
        return default

    def expected_goals(self, home: str, away: str) -> tuple[float, float]:
        home = canon_team(home)
        away = canon_team(away)
        att_h = self._team_lookup(home, self.attack)
        def_a = self._team_lookup(away, self.defence)
        att_a = self._team_lookup(away, self.attack)
        def_h = self._team_lookup(home, self.defence)
        lam_home = float(np.exp(self.intercept + att_h + def_a + self.home_advantage))
        lam_away = float(np.exp(self.intercept + att_a + def_h))
        # Guard against blow-ups for unknown teams.
        lam_home = max(min(lam_home, 6.0), 0.2)
        lam_away = max(min(lam_away, 6.0), 0.1)
        return lam_home, lam_away

    def market_probabilities(self, home: str, away: str) -> dict:
        lam_h, lam_a = self.expected_goals(home, away)

        # Independent Poisson scoreline grid up to MAX_GOALS each.
        ks = np.arange(0, MAX_GOALS + 1)
        ph = poisson.pmf(ks, lam_h)
        pa = poisson.pmf(ks, lam_a)
        grid = np.outer(ph, pa)  # rows = home goals, cols = away goals

        p_btts = float(grid[1:, 1:].sum())
        # Over 2.5 = total goals >= 3.
        idx_h, idx_a = np.indices(grid.shape)
        total = idx_h + idx_a
        p_over_25 = float(grid[total > 2.5].sum())
        p_under_25 = 1.0 - p_over_25

        # Outcome probs (a useful sanity-check against the classifier).
        p_home = float(grid[np.tril_indices_from(grid, k=-1)].sum())
        p_away = float(grid[np.triu_indices_from(grid, k=1)].sum())
        p_draw = float(np.trace(grid))

        # Top-5 most likely scorelines.
        flat = [(int(h), int(a), float(grid[h, a])) for h in ks for a in ks]
        flat.sort(key=lambda t: t[2], reverse=True)
        top_scores = [{"score": f"{h}-{a}", "prob": p} for h, a, p in flat[:5]]

        return {
            "expected_home_goals": lam_h,
            "expected_away_goals": lam_a,
            "p_btts": p_btts,
            "p_over_25": p_over_25,
            "p_under_25": p_under_25,
            "poisson_p_home": p_home,
            "poisson_p_draw": p_draw,
            "poisson_p_away": p_away,
            "p_correct_score_top": top_scores,
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: Path = GOAL_MODEL_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: Path = GOAL_MODEL_PATH) -> "PoissonGoalModel":
        return joblib.load(path)


_goal_model: Optional[PoissonGoalModel] = None


def get_goal_model() -> PoissonGoalModel:
    global _goal_model
    if _goal_model is None:
        if not GOAL_MODEL_PATH.exists():
            # Fit on-the-fly from history; cheap enough (~seconds).
            df = load_all_history()
            if df.empty:
                raise RuntimeError(
                    "Cannot fit Poisson goal model: no data in backend/data/raw. "
                    "Run `python -m ml.download_data` first."
                )
            gm = PoissonGoalModel().fit(df)
            gm.save()
            _goal_model = gm
        else:
            _goal_model = PoissonGoalModel.load()
    return _goal_model
