"""CRUD helpers for the predictions history table."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import PredictionRecord


def create_prediction(
    db: Session,
    *,
    session_id: str | None,
    home_team: str,
    away_team: str,
    fixture_id: int | None,
    referee: str | None,
    kickoff_iso: str | None,
    p_home: float,
    p_draw: float,
    p_away: float,
    predicted_outcome: str,
    confidence: float,
    expected_home_goals: float | None,
    expected_away_goals: float | None,
    p_btts: float | None,
    p_over_25: float | None,
    shap_top: Iterable[dict] | None,
) -> PredictionRecord:
    rec = PredictionRecord(
        session_id=session_id,
        home_team=home_team,
        away_team=away_team,
        fixture_id=fixture_id,
        referee=referee,
        kickoff_iso=kickoff_iso,
        p_home=p_home,
        p_draw=p_draw,
        p_away=p_away,
        predicted_outcome=predicted_outcome,
        confidence=confidence,
        expected_home_goals=expected_home_goals,
        expected_away_goals=expected_away_goals,
        p_btts=p_btts,
        p_over_25=p_over_25,
        shap_top_json=json.dumps(list(shap_top)) if shap_top is not None else None,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def list_predictions(db: Session, session_id: str | None = None, limit: int = 100) -> list[PredictionRecord]:
    q = db.query(PredictionRecord)
    if session_id:
        q = q.filter(PredictionRecord.session_id == session_id)
    return q.order_by(desc(PredictionRecord.created_at)).limit(limit).all()


def resolve_prediction(
    db: Session, pred_id: int, *, home_goals: int, away_goals: int
) -> PredictionRecord | None:
    rec = db.query(PredictionRecord).filter(PredictionRecord.id == pred_id).one_or_none()
    if rec is None:
        return None
    if home_goals > away_goals:
        actual = "HOME"
    elif home_goals < away_goals:
        actual = "AWAY"
    else:
        actual = "DRAW"
    rec.actual_home_goals = home_goals
    rec.actual_away_goals = away_goals
    rec.actual_outcome = actual
    rec.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec


def accuracy(db: Session, session_id: str | None = None) -> dict:
    q = db.query(PredictionRecord).filter(PredictionRecord.actual_outcome.is_not(None))
    if session_id:
        q = q.filter(PredictionRecord.session_id == session_id)
    rows = q.all()
    total = len(rows)
    correct = sum(1 for r in rows if r.predicted_outcome == r.actual_outcome)
    return {"total": total, "correct": correct, "accuracy": (correct / total) if total else None}
