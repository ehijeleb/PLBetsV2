"""SQLAlchemy engine, session, base, and table models."""
from __future__ import annotations

from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


settings = get_settings()

# SQLite needs check_same_thread=False for FastAPI's threaded workers
_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


class PredictionRecord(Base):
    """One row per prediction returned to the user."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_id = Column(String(64), index=True, nullable=True)

    home_team = Column(String(80), nullable=False, index=True)
    away_team = Column(String(80), nullable=False, index=True)
    fixture_id = Column(Integer, nullable=True, index=True)
    referee = Column(String(120), nullable=True)
    kickoff_iso = Column(String(40), nullable=True)

    p_home = Column(Float, nullable=False)
    p_draw = Column(Float, nullable=False)
    p_away = Column(Float, nullable=False)
    predicted_outcome = Column(String(8), nullable=False)  # HOME | DRAW | AWAY
    confidence = Column(Float, nullable=False)

    expected_home_goals = Column(Float, nullable=True)
    expected_away_goals = Column(Float, nullable=True)
    p_btts = Column(Float, nullable=True)
    p_over_25 = Column(Float, nullable=True)

    shap_top_json = Column(Text, nullable=True)  # serialised top features

    # Filled in later by the resolver, once the match has been played
    actual_outcome = Column(String(8), nullable=True)
    actual_home_goals = Column(Integer, nullable=True)
    actual_away_goals = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
