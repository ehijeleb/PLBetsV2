# PLBets v2

Real-time Premier League intelligence dashboard. Predicts match outcomes with an
**XGBoost + LightGBM + RandomForest** soft-vote ensemble, explains every prediction
via **SHAP**, and derives BTTS / Over–Under / scoreline markets from a **Poisson
goal model** — all fronted by a dark, editorial UI built on Next.js 14.

```
┌───────────────────────────────────────────────────────────────┐
│  Next.js 14 + Tailwind + Framer Motion + Recharts (frontend)  │
│                                                               │
│                 ▲  SWR · /api/* JSON                          │
│  FastAPI (async, typed) + APScheduler                         │
│   ├── football-data.org client (TTL on-disk cache)            │
│   ├── pandas feature engineering (rolling 5, season ctx,      │
│   │     H2H, referee, kickoff)                                │
│   ├── EnsembleModel (XGB + LGB + RF, soft-voted)              │
│   ├── SHAP TreeExplainer for top-5 feature contributions      │
│   ├── PoissonGoalModel (Dixon-Coles-lite, λ_home / λ_away)    │
│   └── SQLAlchemy + SQLite for prediction history              │
└───────────────────────────────────────────────────────────────┘
```

## What's in this repo

```
plbets-v2/
├── backend/                FastAPI + ML
│   ├── app/
│   │   ├── routers/        fixtures, predict, stats, history
│   │   ├── services/       football_api, data_loader,
│   │   │                   feature_engineering, model, goal_model
│   │   ├── models/         Pydantic schemas
│   │   ├── db/             SQLAlchemy + CRUD
│   │   └── main.py         FastAPI entry + scheduler
│   ├── ml/
│   │   ├── download_data.py  Pull seasons from football-data.co.uk
│   │   └── train.py          End-to-end training script
│   ├── data/
│   │   ├── raw/           E0_YYYY-YY.csv (filled by download script)
│   │   ├── processed/     Reserved for feature parquet snapshots
│   │   └── cache/         Football-data.org JSON cache
│   └── requirements.txt
│
├── frontend/               Next.js 14 (App Router) + Tailwind
│   ├── app/                page.tsx · stats/page.tsx · history/page.tsx
│   ├── components/         UI primitives + result components
│   └── lib/                api.ts · types.ts
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Quick start (local)

### Prerequisites

| Tool       | Version  | Notes                                                       |
| ---------- | -------- | ----------------------------------------------------------- |
| Python     | 3.11+ (3.14 tested) | A virtualenv is created in `backend/.venv`     |
| Node.js    | 20+ (24 tested)     | LTS recommended                                |
| Docker     | optional | Only needed for the one-command `docker compose up` path    |

> **Tip:** if pip fails with `Could not find a suitable TLS CA certificate bundle`,
> unset `CURL_CA_BUNDLE` first (Windows users may have it pinned to a stray
> Postgres install): `unset CURL_CA_BUNDLE` (bash) or `Remove-Item Env:\CURL_CA_BUNDLE` (PowerShell).

### 1. Configure environment

```bash
cp .env.example .env
# Open .env and paste your free football-data.org key into FOOTBALL_DATA_API_KEY
# (Sign up at https://www.football-data.org/client/register — the free tier is enough.)
```

The frontend reads `NEXT_PUBLIC_API_URL` from the **same** `.env` file when run
via `docker compose`. When you run `npm run dev` directly, copy
`frontend/.env.local.example` to `frontend/.env.local` instead.

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

# Download last 5 seasons of Premier League CSVs into data/raw/
python -m ml.download_data --seasons 5

# Train the ensemble + Poisson model (saves to backend/models_out/)
python -m ml.train --skip-download

# Boot the API
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Visit `http://127.0.0.1:8000/docs` for the auto-generated OpenAPI explorer, or
`http://127.0.0.1:8000/health` to verify the model loaded and CSVs are in place.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local      # only if you want to override the API URL
npm run dev
```

Then open **http://localhost:3000**.

---

## Endpoints

| Method | Path                              | Description                                   |
| ------ | --------------------------------- | --------------------------------------------- |
| GET    | `/api/fixtures/upcoming`          | Next gameweek fixtures (live)                 |
| GET    | `/api/fixtures/{id}`              | One fixture                                   |
| GET    | `/api/teams`                      | All PL teams + crests (from football-data.org)|
| GET    | `/api/standings`                  | Current PL table                              |
| POST   | `/api/predict`                    | **Generate a prediction** (main endpoint)     |
| GET    | `/api/predict/history`            | Past predictions (per-session)                |
| POST   | `/api/predict/history/{id}/resolve` | Mark a prediction with the real result      |
| GET    | `/api/stats/form/{team}`          | Recent form (last N matches)                  |
| GET    | `/api/stats/h2h/{home}/{away}`    | Head-to-head history                          |
| GET    | `/api/stats/form-heatmap`         | W/D/L grid across all teams                   |
| GET    | `/api/stats/home-vs-away`         | Per-team home/away win rates                  |
| GET    | `/api/stats/teams`                | Team names known to the local history         |
| GET    | `/api/stats/referees`             | Referees from the local history               |

### Example: predict

```bash
curl -X POST http://127.0.0.1:8000/api/predict \
  -H 'Content-Type: application/json' \
  -d '{"home_team":"Arsenal","away_team":"Liverpool"}'
```

Returns probabilities, predicted outcome, confidence band, the top-5 SHAP
features (with human-readable labels), Poisson-derived expected goals + BTTS /
Over-Under markets, and recent form / H2H summaries.

---

## Training the model

```bash
python -m ml.train --seasons 5       # download + train end-to-end (default)
python -m ml.train --skip-download   # use whatever's already in data/raw/
```

Outputs:

- `backend/models_out/model.pkl`     — the XGB + LGB + RF ensemble
- `backend/models_out/goal_model.pkl` — the Poisson goal model

The training pipeline is **time-aware**: features for each match are built from
matches strictly prior to it, so nothing leaks forward. The pipeline currently
runs on the 1,880-match window of the last five completed seasons in about
~90 seconds for feature engineering + ~10 seconds for model fitting.

To add a new season, drop its CSV into `backend/data/raw/` (filename pattern
`E0_<YYYY-YY>.csv`) or rerun `python -m ml.download_data --seasons 6`.

---

## Environment variables (all)

| Variable                 | Where     | Default                                     | Notes                                                  |
| ------------------------ | --------- | ------------------------------------------- | ------------------------------------------------------ |
| `FOOTBALL_DATA_API_KEY`  | backend   | _empty_                                     | Free key from football-data.org                        |
| `DATABASE_URL`           | backend   | `sqlite:///./plbets.db`                     | SQLAlchemy URL                                         |
| `CORS_ORIGINS`           | backend   | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated origins                            |
| `NEXT_PUBLIC_API_URL`    | frontend  | `http://localhost:8000`                     | Where the browser calls the API                        |

---

## Docker Compose

The repo ships with a `docker-compose.yml` that builds the backend (Python 3.12
slim + ML stack) and frontend (Node 20 alpine) and wires them together with a
single command:

```bash
docker compose up --build
```

> **Verified locally:** the FastAPI + Next.js dev servers were booted natively
> (Python 3.14 venv + Node 20) and all endpoints / pages returned `200`.
> Docker isn't installed on the build machine, so `docker compose up` itself
> hasn't been exercised here — but the compose file and Dockerfiles are
> straightforward (slim base images, `pip install -r requirements.txt`,
> `npm ci`, `npm run dev` / `uvicorn app.main:app`).

When the backend container starts and finds no `model.pkl`, it will run
`python -m ml.train --seasons 5` once before starting uvicorn — first boot is
therefore a few minutes longer than subsequent boots. The `data/` and
`models_out/` directories are mounted as volumes so trained artefacts survive
container restarts.

---

## Production deployment (Vercel + Render + Supabase)

The repo ships with a `render.yaml` blueprint and a `.github/workflows/retrain.yml`
GitHub Action that together make the production path one-click.

### Supabase (database)

1. Create a project at [supabase.com](https://supabase.com).
2. **Settings → Database → Connection string → URI**. Choose the **Connection
   pooler** option (port 6543, transaction mode).
3. Prefix the URL with `postgresql+psycopg2://` so SQLAlchemy picks the right
   driver. Example:
   ```
   postgresql+psycopg2://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```
4. No migrations needed — FastAPI's `init_db()` creates the one `predictions`
   table on first boot.

### Render (backend)

1. Push the repo to GitHub.
2. In Render: **New → Blueprint** → point at the repo. Render reads
   [`render.yaml`](render.yaml) and creates the `plbets-backend` web service.
3. Set the three secrets in the service's **Environment** tab:
   - `FOOTBALL_DATA_API_KEY` — your football-data.org key
   - `DATABASE_URL` — the Supabase pooler URL from above
   - `CORS_ORIGINS` — `https://<your-app>.vercel.app,http://localhost:3000`
4. Free tier sleeps after 15 min idle (first prediction after a nap takes
   ~30 s while Python and the model warm up). Bump to **Starter ($7/mo)** for
   always-on.

The Dockerfile reads `$PORT` from Render's environment and expects
`models_out/model.pkl` to be committed (it fails loudly otherwise — training in
production is too slow). The weekly GitHub Action keeps the committed model
fresh.

### Vercel (frontend)

1. **New Project** → import the repo → set **Root Directory** to `frontend`.
2. Framework preset is auto-detected as Next.js. No build config needed.
3. Env var: `NEXT_PUBLIC_API_URL=https://<your-render-service>.onrender.com`.
4. Deploy.

### Weekly model retraining

[`.github/workflows/retrain.yml`](.github/workflows/retrain.yml) runs every
Tuesday at 03:00 UTC (after the weekend's matches settle and
football-data.co.uk publishes the updated CSV):

- Downloads the last 5 seasons' CSVs from football-data.co.uk
- Runs `python -m ml.train`
- Commits the new `model.pkl` and `goal_model.pkl` straight to `main`
- Render's auto-deploy picks up the commit and ships the new model

You can also trigger it manually from the **Actions** tab → **Weekly model
retrain** → **Run workflow**. The workflow needs no secrets — football-data.co.uk
is unauthenticated and the action commits via `GITHUB_TOKEN`.

---

## Design system

CSS variables (see [`frontend/app/globals.css`](frontend/app/globals.css)):

| Variable          | Value     | Use                                  |
| ----------------- | --------- | ------------------------------------ |
| `--bg-primary`    | `#0A0E1A` | Page background (near-black navy)    |
| `--bg-secondary`  | `#111827` | Card surface                         |
| `--bg-tertiary`   | `#1F2937` | Elevated surfaces                    |
| `--accent-green`  | `#00FF87` | Primary CTA, home-win signal         |
| `--accent-amber`  | `#F59E0B` | Draws / caution                      |
| `--accent-red`    | `#EF4444` | Away-win signal                      |
| `--text-primary`  | `#F9FAFB` | Body text                            |
| `--text-muted`    | `#6B7280` | Labels                               |
| `--border`        | `#1F2937` | Hairline rules                       |

Fonts: **Bebas Neue** (display), **DM Sans** (body), **JetBrains Mono** (numbers
/ odds) — all loaded from Google Fonts in `globals.css`.

---

## Responsible gambling

Every betting-related output in the UI carries this notice (also baked into the
`BettingInsightBox` component):

> ⚠ For informational and entertainment purposes only. Gambling can be addictive.
> Please bet responsibly. [GamStop](https://www.gamstop.co.uk) ·
> [BeGambleAware](https://www.begambleaware.org)

---

## Limitations / known gaps

- **Live fixture / standings data needs an API key.** Without
  `FOOTBALL_DATA_API_KEY` set, the upcoming-fixtures row and the league table on
  `/stats` will be empty (the rest of the app — manual predictions, SHAP, form
  heatmap, history — still works using the local CSV history).
- **First-time training is single-threaded for feature engineering** (~90 s on a
  typical laptop). Once `model.pkl` exists, predictions are <100 ms.
- **History is per-browser session.** A random session ID is stored in
  `localStorage` so different browsers see different prediction histories.
  There's no user auth — the brief explicitly didn't ask for it.
