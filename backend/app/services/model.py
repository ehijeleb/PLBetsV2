"""Stacked ensemble (XGB + LGB + RF) for 3-class outcome prediction.

Why hand-rolled instead of `VotingClassifier`? Because we want each base model
to remain individually accessible — XGBoost in particular powers the SHAP
explanations, and that's far cleaner when we keep the model object around
instead of nesting it inside a meta-estimator.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from app.config import MODELS_DIR
from app.services.feature_engineering import FEATURE_COLUMNS, FEATURE_LABELS

logger = logging.getLogger(__name__)


MODEL_PATH = MODELS_DIR / "model.pkl"

CLASS_HOME, CLASS_DRAW, CLASS_AWAY = 0, 1, 2
CLASS_LABELS = {CLASS_HOME: "HOME", CLASS_DRAW: "DRAW", CLASS_AWAY: "AWAY"}


@dataclass
class EnsembleModel:
    feature_columns: list[str] = field(default_factory=lambda: list(FEATURE_COLUMNS))
    weights: tuple[float, float, float] = (1.0, 1.5, 1.5)   # rf, xgb, lgb
    rf: object | None = None
    xgb: object | None = None
    lgb: object | None = None
    classes_: list[int] = field(default_factory=lambda: [CLASS_HOME, CLASS_DRAW, CLASS_AWAY])
    _explainer: object | None = field(default=None, repr=False)

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "EnsembleModel":
        from sklearn.ensemble import RandomForestClassifier
        import xgboost as xgb_lib
        import lightgbm as lgb_lib

        self.rf = RandomForestClassifier(
            n_estimators=300, max_depth=8, random_state=42, n_jobs=-1, class_weight="balanced_subsample",
        )
        self.xgb = xgb_lib.XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            tree_method="hist",
            random_state=42,
            n_jobs=-1,
        )
        self.lgb = lgb_lib.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            objective="multiclass",
            num_class=3,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )

        X = X[self.feature_columns]
        print("  - fitting RandomForest...")
        self.rf.fit(X, y)
        print("  - fitting XGBoost...")
        self.xgb.fit(X, y)
        print("  - fitting LightGBM...")
        self.lgb.fit(X, y)
        return self

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X = X[self.feature_columns]
        w_rf, w_xgb, w_lgb = self.weights
        total = w_rf + w_xgb + w_lgb
        p_rf = self.rf.predict_proba(X)
        p_xgb = self.xgb.predict_proba(X)
        p_lgb = self.lgb.predict_proba(X)
        return (w_rf * p_rf + w_xgb * p_xgb + w_lgb * p_lgb) / total

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.predict_proba(X).argmax(axis=1)

    # ── SHAP explainability ───────────────────────────────────────────────────

    def _ensure_explainer(self) -> object:
        if self._explainer is None:
            import shap
            self._explainer = shap.TreeExplainer(self.xgb)
        return self._explainer

    def explain_top_features(self, x_row: pd.Series, top_k: int = 5) -> list[dict]:
        """Return the top-k features by |SHAP value| for the most likely class.

        Each entry is `{feature, label, shap_value, contribution}` where
        contribution is the class name (home/draw/away) the feature pushed toward.
        """
        explainer = self._ensure_explainer()
        x_df = pd.DataFrame([x_row[self.feature_columns]], columns=self.feature_columns)
        sv = explainer.shap_values(x_df)

        # XGB TreeExplainer for multiclass returns either a list-of-arrays (per class)
        # OR a single 3-D ndarray (n_rows, n_features, n_classes), depending on version.
        if isinstance(sv, list):
            shap_per_class = np.stack([np.asarray(s)[0] for s in sv], axis=0)  # (3, n_features)
        else:
            arr = np.asarray(sv)
            if arr.ndim == 3:
                shap_per_class = arr[0].T   # (n_classes, n_features)
            else:
                # Binary-style fallback — promote to 3 classes by repeating.
                shap_per_class = np.stack([arr[0]] * 3, axis=0)

        # Pick the class the model thinks is most likely for this single row.
        probs = self.predict_proba(x_df)[0]
        top_class = int(np.argmax(probs))
        contributions_for_top = shap_per_class[top_class]

        order = np.argsort(np.abs(contributions_for_top))[::-1][:top_k]
        out: list[dict] = []
        for idx in order:
            feat = self.feature_columns[int(idx)]
            val = float(contributions_for_top[int(idx)])
            # Which class did this feature push hardest toward (across all classes)?
            class_pushed = int(np.argmax(shap_per_class[:, int(idx)]))
            out.append(
                {
                    "feature": feat,
                    "label": FEATURE_LABELS.get(feat, feat),
                    "shap_value": val,
                    "contribution": CLASS_LABELS[class_pushed].lower(),
                }
            )
        return out

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: Path = MODEL_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "EnsembleModel":
        obj = joblib.load(path)
        if not isinstance(obj, cls):
            raise RuntimeError(f"Loaded object is {type(obj)}, expected EnsembleModel")
        return obj


# ─── Module-level singleton (lazy) ────────────────────────────────────────────

_model: Optional[EnsembleModel] = None


def get_model() -> EnsembleModel:
    """Return the cached EnsembleModel, loading from disk on first access.

    Raises a clear RuntimeError if the model hasn't been trained yet.
    """
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(
                f"model.pkl not found at {MODEL_PATH}. Run `python -m ml.train` to train it."
            )
        _model = EnsembleModel.load(MODEL_PATH)
        logger.info("EnsembleModel loaded from %s", MODEL_PATH)
    return _model


def confidence_band(p: float) -> str:
    if p >= 0.6:
        return "HIGH"
    if p >= 0.45:
        return "MEDIUM"
    return "LOW"
