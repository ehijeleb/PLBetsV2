"""Stand-alone training script.

Runs end-to-end:
    1. Downloads recent CSVs (via ml/download_data.py) if any are missing.
    2. Loads + concatenates them through services/data_loader.py.
    3. Builds the engineered feature matrix.
    4. Fits the XGB+LGB+RF ensemble.
    5. Fits the Poisson goal model.
    6. Saves both to backend/models_out/.

Usage:
    python -m ml.train               # train on whatever's in data/raw/
    python -m ml.train --seasons 6   # ensure 6 recent seasons are present first
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow running both as `python -m ml.train` and `python ml/train.py`
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.services.data_loader import list_available_csvs, reload_history          # noqa: E402
from app.services.feature_engineering import build_training_matrix                # noqa: E402
from app.services.goal_model import PoissonGoalModel, GOAL_MODEL_PATH              # noqa: E402
from app.services.model import EnsembleModel, MODEL_PATH                          # noqa: E402
from ml.download_data import download_seasons                                     # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PLBets v2 ensemble + goal model")
    parser.add_argument("--seasons", type=int, default=5, help="How many recent seasons to ensure on disk")
    parser.add_argument("--skip-download", action="store_true", help="Skip ml.download_data call")
    args = parser.parse_args()

    if not args.skip_download:
        existing = list_available_csvs()
        if len(existing) < args.seasons:
            print(f"[1/5] Downloading {args.seasons} seasons of PL CSVs...")
            download_seasons(args.seasons)
        else:
            print(f"[1/5] {len(existing)} CSVs already present — skipping download.")
    else:
        print("[1/5] Skipping download (--skip-download).")

    print("[2/5] Loading + normalising history...")
    df = reload_history()
    if df.empty:
        print("ERROR: No history loaded. Place E0_*.csv files in backend/data/raw/ or re-run without --skip-download.")
        sys.exit(1)
    print(f"      {len(df):,} matches across {df['season'].nunique() if 'season' in df.columns else '?'} season(s)")

    print("[3/5] Building engineered feature matrix...")
    t = time.time()
    X, y = build_training_matrix(df)
    print(f"      X={X.shape}, y={y.shape} in {time.time() - t:.1f}s")

    print("[4/5] Fitting XGB + LGB + RF ensemble...")
    t = time.time()
    model = EnsembleModel().fit(X, y)
    saved = model.save(MODEL_PATH)
    print(f"      Trained in {time.time() - t:.1f}s, saved to {saved}")

    print("[5/5] Fitting Poisson goal model...")
    t = time.time()
    goal = PoissonGoalModel().fit(df)
    saved_g = goal.save(GOAL_MODEL_PATH)
    print(f"      Trained in {time.time() - t:.1f}s, saved to {saved_g}")

    # Quick sanity prediction.
    sample = X.tail(1)
    probs = model.predict_proba(sample)[0]
    print(f"\nSanity check on last training row: HOME {probs[0]:.2%}  DRAW {probs[1]:.2%}  AWAY {probs[2]:.2%}")
    print("Done.")


if __name__ == "__main__":
    main()
