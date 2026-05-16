"""Pydantic schemas for the FastAPI surface."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ─── Teams & fixtures ─────────────────────────────────────────────────────────

class Team(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    tla: Optional[str] = None
    crest: Optional[str] = None


class Fixture(BaseModel):
    id: int
    matchday: Optional[int] = None
    status: str
    utc_date: datetime
    home_team: Team
    away_team: Team
    competition: str = "Premier League"
    venue: Optional[str] = None
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None


# ─── Standings ────────────────────────────────────────────────────────────────

class StandingRow(BaseModel):
    position: int
    team: Team
    played: int
    won: int
    draw: int
    lost: int
    points: int
    goals_for: int
    goals_against: int
    goal_difference: int
    form: Optional[str] = None


class Standings(BaseModel):
    season: Optional[str] = None
    rows: list[StandingRow]


# ─── Form / H2H ───────────────────────────────────────────────────────────────

class FormMatch(BaseModel):
    date: datetime
    opponent: str
    venue: Literal["H", "A"]
    goals_for: int
    goals_against: int
    result: Literal["W", "D", "L"]


class TeamForm(BaseModel):
    team: str
    matches: list[FormMatch]
    wins: int
    draws: int
    losses: int
    goals_scored: int
    goals_conceded: int
    clean_sheets: int


class H2HMatch(BaseModel):
    date: datetime
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    venue: Optional[str] = None


class H2H(BaseModel):
    home_team: str
    away_team: str
    matches: list[H2HMatch]
    home_wins: int
    draws: int
    away_wins: int


# ─── Prediction ───────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    home_team: str = Field(..., min_length=2)
    away_team: str = Field(..., min_length=2)
    fixture_id: Optional[int] = None
    referee: Optional[str] = None
    kickoff: Optional[datetime] = None
    session_id: Optional[str] = None


class ShapFeature(BaseModel):
    feature: str
    label: str
    shap_value: float
    contribution: Literal["home", "draw", "away"]


class GoalMarkets(BaseModel):
    expected_home_goals: float
    expected_away_goals: float
    p_btts: float
    p_over_25: float
    p_under_25: float
    p_correct_score_top: list[dict]  # [{score: "2-1", prob: 0.12}, ...]


class PredictResponse(BaseModel):
    id: Optional[int] = None
    home_team: str
    away_team: str
    p_home: float
    p_draw: float
    p_away: float
    predicted_outcome: Literal["HOME", "DRAW", "AWAY"]
    confidence: float
    confidence_band: Literal["LOW", "MEDIUM", "HIGH"]
    shap_top: list[ShapFeature]
    goal_markets: GoalMarkets
    home_form: Optional[TeamForm] = None
    away_form: Optional[TeamForm] = None
    h2h: Optional[H2H] = None


# ─── History ──────────────────────────────────────────────────────────────────

class HistoryRow(BaseModel):
    id: int
    created_at: datetime
    home_team: str
    away_team: str
    predicted_outcome: str
    p_home: float
    p_draw: float
    p_away: float
    confidence: float
    actual_outcome: Optional[str] = None
    actual_home_goals: Optional[int] = None
    actual_away_goals: Optional[int] = None
    correct: Optional[bool] = None


class HistoryResponse(BaseModel):
    rows: list[HistoryRow]
    total: int
    correct: int
    accuracy: Optional[float] = None
