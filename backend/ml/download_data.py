"""Download historical Premier League CSVs from football-data.co.uk.

Each season is a single CSV at https://www.football-data.co.uk/mmz4281/<season>/E0.csv
where <season> is e.g. ``2021`` for the 2020/21 season (the year the season ENDS).
Files land in backend/data/raw/E0_<YYYY-YY>.csv.

Run directly:

    python -m ml.download_data --seasons 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

# Allow running both as `python -m ml.download_data` and `python ml/download_data.py`
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.config import RAW_DATA_DIR  # noqa: E402

BASE = "https://www.football-data.co.uk/mmz4281"


def season_code(end_year: int) -> str:
    """End year 2025 -> '2425' (the directory used by football-data.co.uk)."""
    start = (end_year - 1) % 100
    end = end_year % 100
    return f"{start:02d}{end:02d}"


def season_label(end_year: int) -> str:
    """End year 2025 -> '2024-25' (used in our local filename)."""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def download_season(end_year: int, *, force: bool = False) -> Path | None:
    code = season_code(end_year)
    label = season_label(end_year)
    url = f"{BASE}/{code}/E0.csv"
    dest = RAW_DATA_DIR / f"E0_{label}.csv"

    if dest.exists() and not force and dest.stat().st_size > 1024:
        print(f"  [ok]   already have {dest.name} ({dest.stat().st_size:,} bytes)")
        return dest

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            r = client.get(url)
        if r.status_code != 200:
            print(f"  [fail] {label}: HTTP {r.status_code} from {url}")
            return None
        body = r.content
        if len(body) < 1024 or b"Date" not in body[:200]:
            print(f"  [fail] {label}: response too small or missing header from {url}")
            return None
        dest.write_bytes(body)
        print(f"  [ok]   {label}: saved {dest.name} ({len(body):,} bytes)")
        return dest
    except Exception as exc:
        print(f"  [fail] {label}: download failed: {exc}")
        return None


def download_seasons(n: int = 5, end_year: int | None = None) -> list[Path]:
    """Download the most recent `n` completed Premier League seasons."""
    from datetime import datetime

    if end_year is None:
        today = datetime.utcnow()
        end_year = today.year if today.month >= 8 else today.year
    years = list(range(end_year, end_year - n, -1))
    print(f"Downloading {n} seasons to {RAW_DATA_DIR}:")
    saved: list[Path] = []
    for y in years:
        p = download_season(y)
        if p is not None:
            saved.append(p)
    print(f"\nDone. {len(saved)}/{len(years)} seasons available locally.")
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Download PL CSVs from football-data.co.uk")
    parser.add_argument("--seasons", type=int, default=5, help="How many recent seasons to grab")
    parser.add_argument("--end-year", type=int, default=None, help="Latest season-end year (e.g. 2025)")
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    args = parser.parse_args()

    from datetime import datetime

    end_year = args.end_year or (datetime.utcnow().year if datetime.utcnow().month >= 8 else datetime.utcnow().year)
    years = list(range(end_year, end_year - args.seasons, -1))
    for y in years:
        download_season(y, force=args.force)


if __name__ == "__main__":
    main()
