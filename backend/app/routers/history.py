"""Prediction-history endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import crud
from app.db.database import get_db
from app.models.schemas import HistoryResponse, HistoryRow


router = APIRouter(prefix="/api/predict", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def history(session_id: str | None = None, limit: int = 100, db: Session = Depends(get_db)) -> HistoryResponse:
    rows = crud.list_predictions(db, session_id=session_id, limit=limit)
    metrics = crud.accuracy(db, session_id=session_id)
    out = [
        HistoryRow(
            id=r.id,
            created_at=r.created_at,
            home_team=r.home_team,
            away_team=r.away_team,
            predicted_outcome=r.predicted_outcome,
            p_home=r.p_home,
            p_draw=r.p_draw,
            p_away=r.p_away,
            confidence=r.confidence,
            actual_outcome=r.actual_outcome,
            actual_home_goals=r.actual_home_goals,
            actual_away_goals=r.actual_away_goals,
            correct=(r.actual_outcome == r.predicted_outcome) if r.actual_outcome else None,
        )
        for r in rows
    ]
    return HistoryResponse(rows=out, total=metrics["total"], correct=metrics["correct"], accuracy=metrics["accuracy"])


@router.post("/history/{pred_id}/resolve")
async def resolve(pred_id: int, home_goals: int, away_goals: int, db: Session = Depends(get_db)) -> dict:
    rec = crud.resolve_prediction(db, pred_id, home_goals=home_goals, away_goals=away_goals)
    if not rec:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"id": rec.id, "actual": rec.actual_outcome, "correct": rec.actual_outcome == rec.predicted_outcome}
