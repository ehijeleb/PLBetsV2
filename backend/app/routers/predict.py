"""Main prediction endpoint — wires the classifier ensemble, SHAP, the Poisson
goal model, and recent-form context into a single response.
"""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import crud
from app.db.database import get_db
from app.models.schemas import PredictRequest, PredictResponse
from app.services.data_loader import canon_team, load_all_history
from app.services.feature_engineering import (
    FEATURE_COLUMNS,
    build_features_for_match,
)
from app.services.goal_model import get_goal_model
from app.services.model import CLASS_LABELS, confidence_band, get_model


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predict", tags=["predict"])


def _team_form_summary(team: str, *, home: bool, n: int = 5) -> dict | None:
    df = load_all_history()
    if df.empty:
        return None
    team = canon_team(team)
    col = "home" if home else "away"
    games = df[df[col] == team].sort_values("date").tail(n)
    if games.empty:
        return None
    matches = []
    wins = draws = losses = gs = gc = cs = 0
    for _, r in games.iterrows():
        if home:
            gf, ga, opp = int(r["fthg"]), int(r["ftag"]), r["away"]
            res = "W" if r["ftr"] == "H" else ("D" if r["ftr"] == "D" else "L")
            venue = "H"
        else:
            gf, ga, opp = int(r["ftag"]), int(r["fthg"]), r["home"]
            res = "W" if r["ftr"] == "A" else ("D" if r["ftr"] == "D" else "L")
            venue = "A"
        wins += res == "W"
        draws += res == "D"
        losses += res == "L"
        gs += gf
        gc += ga
        cs += ga == 0
        matches.append(
            {
                "date": r["date"].to_pydatetime(),
                "opponent": opp,
                "venue": venue,
                "goals_for": gf,
                "goals_against": ga,
                "result": res,
            }
        )
    return {
        "team": team,
        "matches": matches,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_scored": gs,
        "goals_conceded": gc,
        "clean_sheets": cs,
    }


def _h2h_summary(home: str, away: str, n: int = 5) -> dict | None:
    df = load_all_history()
    if df.empty:
        return None
    home_c, away_c = canon_team(home), canon_team(away)
    mask = ((df["home"] == home_c) & (df["away"] == away_c)) | ((df["home"] == away_c) & (df["away"] == home_c))
    games = df[mask].sort_values("date").tail(n)
    if games.empty:
        return {"home_team": home_c, "away_team": away_c, "matches": [], "home_wins": 0, "draws": 0, "away_wins": 0}
    matches = []
    home_wins = draws = away_wins = 0
    for _, r in games.iterrows():
        if r["home"] == home_c:
            hg, ag = int(r["fthg"]), int(r["ftag"])
            h_name, a_name = home_c, away_c
        else:
            hg, ag = int(r["fthg"]), int(r["ftag"])
            h_name, a_name = away_c, home_c
        # Tally from the requested home team's perspective.
        if r["home"] == home_c:
            if hg > ag:
                home_wins += 1
            elif hg < ag:
                away_wins += 1
            else:
                draws += 1
        else:
            if hg > ag:
                away_wins += 1
            elif hg < ag:
                home_wins += 1
            else:
                draws += 1
        matches.append(
            {
                "date": r["date"].to_pydatetime(),
                "home_team": h_name,
                "away_team": a_name,
                "home_goals": hg,
                "away_goals": ag,
                "venue": None,
            }
        )
    return {
        "home_team": home_c,
        "away_team": away_c,
        "matches": matches,
        "home_wins": home_wins,
        "draws": draws,
        "away_wins": away_wins,
    }


@router.post("", response_model=PredictResponse)
async def predict(req: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    home, away = canon_team(req.home_team), canon_team(req.away_team)
    if home == away:
        raise HTTPException(status_code=400, detail="Home and away teams must differ.")

    try:
        model = get_model()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    kickoff_ts = pd.Timestamp(req.kickoff) if req.kickoff else pd.Timestamp.utcnow()

    feats = build_features_for_match(
        home_team=home, away_team=away, kickoff=kickoff_ts, referee=req.referee
    )
    X = pd.DataFrame([feats], columns=FEATURE_COLUMNS)
    probs = model.predict_proba(X)[0]
    top_class = int(probs.argmax())
    predicted = CLASS_LABELS[top_class]
    confidence = float(probs[top_class])

    shap_top = model.explain_top_features(X.iloc[0], top_k=5)

    # Goal markets via Poisson.
    try:
        gm = get_goal_model()
        markets = gm.market_probabilities(home, away)
    except Exception as e:
        logger.exception("goal model failed: %s", e)
        markets = {
            "expected_home_goals": 1.5,
            "expected_away_goals": 1.2,
            "p_btts": 0.55,
            "p_over_25": 0.55,
            "p_under_25": 0.45,
            "p_correct_score_top": [],
        }

    home_form = _team_form_summary(home, home=True, n=5)
    away_form = _team_form_summary(away, home=False, n=5)
    h2h = _h2h_summary(home, away, n=5)

    rec = crud.create_prediction(
        db,
        session_id=req.session_id,
        home_team=home,
        away_team=away,
        fixture_id=req.fixture_id,
        referee=req.referee,
        kickoff_iso=req.kickoff.isoformat() if req.kickoff else None,
        p_home=float(probs[0]),
        p_draw=float(probs[1]),
        p_away=float(probs[2]),
        predicted_outcome=predicted,
        confidence=confidence,
        expected_home_goals=markets["expected_home_goals"],
        expected_away_goals=markets["expected_away_goals"],
        p_btts=markets["p_btts"],
        p_over_25=markets["p_over_25"],
        shap_top=shap_top,
    )

    return PredictResponse(
        id=rec.id,
        home_team=home,
        away_team=away,
        p_home=float(probs[0]),
        p_draw=float(probs[1]),
        p_away=float(probs[2]),
        predicted_outcome=predicted,
        confidence=confidence,
        confidence_band=confidence_band(confidence),
        shap_top=shap_top,
        goal_markets={
            "expected_home_goals": markets["expected_home_goals"],
            "expected_away_goals": markets["expected_away_goals"],
            "p_btts": markets["p_btts"],
            "p_over_25": markets["p_over_25"],
            "p_under_25": markets["p_under_25"],
            "p_correct_score_top": markets["p_correct_score_top"],
        },
        home_form=home_form,
        away_form=away_form,
        h2h=h2h,
    )
