# PLBets — Major Revamp Brief for Claude Code

> Hand this document to Claude Code with the instruction: **"Build the revamped PLBets application described in this brief from scratch."**

---

## 1. Current State Assessment

The existing PLBets app is a simple two-panel form:
- Four dropdowns: Home Team, Away Team, Day of Week, Match Time
- One un-populated referee dropdown (broken/empty)
- A single "Predict Match" button
- No visualisation of results, no context, no live data
- Static CSV-based historical data loaded at startup
- A single RandomForestClassifier with no tuning, no feature engineering notes
- No authentication, no persistence, no user history

**Core problem:** The UI is a bare form, the model is a black box, and the output is described in the README as "win-loss records and average goals scored" — which gives users almost nothing to act on.

---

## 2. Vision for the Revamp

Transform PLBets from a static prediction form into a **real-time Premier League intelligence dashboard** — a tool that feels like it belongs alongside the best sports-data products. Users should walk away feeling *informed*, not just given a number.

**Design direction:** Dark, editorial, football-stadium atmosphere. Think the tension of a matchday programme meets a Bloomberg terminal. Deep navy/charcoal base, electric green (`#00FF87`) as the primary accent (echoing Premier League branding), sharp typography, data-dense but readable.

---

## 3. Tech Stack (Revamped)

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** + custom CSS variables
- **Framer Motion** for animations
- **Recharts** for data visualisations
- **SWR** for data fetching / cache

### Backend
- **FastAPI** (replace Flask — async, typed, auto-docs)
- **Python 3.11+**
- **SQLite** (via SQLAlchemy) for user history & cached predictions
- **APScheduler** for background data refresh jobs

### Data
- **football-data.org free API** (live fixtures, real team form) — free tier is sufficient
- Keep historical CSV as fallback/training data
- Fetch upcoming GW fixtures automatically

### ML
- Replace bare RandomForest with an **ensemble pipeline**:
  - XGBoost + LightGBM + Logistic Regression stacked ensemble
  - Proper feature engineering (see Section 5)
  - SHAP values for explainability

---

## 4. UI/UX Revamp — Page by Page

### 4.1 Global Design System

```
CSS Variables to define:
--bg-primary:     #0A0E1A   (near-black navy)
--bg-secondary:   #111827   (card background)
--bg-tertiary:    #1F2937   (elevated surfaces)
--accent-green:   #00FF87   (electric green — primary CTA)
--accent-amber:   #F59E0B   (draw / caution)
--accent-red:     #EF4444   (away win)
--text-primary:   #F9FAFB
--text-muted:     #6B7280
--border:         #1F2937
--font-display:   'Bebas Neue' (Google Fonts — for scores, headers)
--font-body:      'DM Sans'   (Google Fonts — for UI text)
--font-mono:      'JetBrains Mono' (for odds, stats)
```

### 4.2 Landing / Home Page (`/`)

Replace the bare form with a **matchday-style dashboard**:

**Top bar (sticky nav):**
- PLBets logo (monogram "PL" in accent green, bold Bebas Neue)
- Current GW badge (e.g. "GW 32")
- Live clock (UK time)
- Dark/light mode toggle (dark default)

**Hero section — "This Weekend's Fixtures":**
- Automatically fetch the upcoming GW fixtures from the football-data API
- Show a horizontal scrollable row of **Match Cards**
  - Each card: Home crest | Home name | vs | Away name | Away crest
  - Kickoff time & date
  - A **"Analyse"** button per fixture that deep-links to the prediction view
  - A subtle probability bar (home | draw | away) pre-computed in the background
- Skeleton loaders while fetching

**Prediction Panel (replaces the old form):**
- Move the manual team picker here as a **fallback / custom match** input
- Use an autocomplete search input for teams (not a raw `<select>`)
- Teams shown with their actual Premier League crests (fetch from football-data API or CDN)
- Two columns: Home | Away — with a glowing "VS" divider in the centre
- **Remove Day of Week and Match Time from the primary flow** — these should be optional "Advanced Filters" in a collapsible accordion (they have marginal predictive value and clutter the UX)
- Referee selector populated from real 2024/25 referee data

**CTA Button:**
- Large, full-width, electric green button: "**GENERATE PREDICTION**"
- On click: animated loading state with a football spinning icon, then smooth scroll to results

### 4.3 Results / Prediction Output (same page, below fold)

This is where the biggest UX lift happens. Currently the app likely just shows text. Replace with:

**Outcome Probability Card:**
```
╔══════════════════════════════════════════╗
║  Arsenal          vs        Liverpool   ║
║                                          ║
║  HOME WIN    DRAW      AWAY WIN          ║
║  ████████░░  ███░░░░░  █████░░░░         ║
║   54%         18%        28%             ║
║                                          ║
║  ★ PREDICTION: Arsenal Win              ║
║  Confidence: HIGH  ██████████ 87%       ║
╚══════════════════════════════════════════╝
```
- Animated probability bars (Framer Motion width transitions)
- Colour-coded: green = home, amber = draw, red = away
- Confidence score derived from model's class probability spread

**Why This Prediction? — SHAP Explainability Panel**
- Top 5 features driving the prediction, as a horizontal bar chart (Recharts)
- Plain-English labels: "Arsenal's last 5 home wins", "Liverpool away goals conceded", "H2H record", etc.
- This is the **killer feature** — it makes the tool feel trustworthy, not magical

**Team Form Cards (side by side):**
- Last 5 matches as coloured pills: W/D/L
- Goals scored / conceded at home (or away for away team)
- Clean sheet rate
- Key player availability flag (manual input or from API injury data)

**Head-to-Head History:**
- Last 5 meetings shown as a mini timeline
- Result, score, and venue for each
- Rendered as a compact table with colour-coded results

**Betting Insight Box:**
- Clearly labelled: *"For informational purposes only. Bet responsibly."*
- Maps model output to typical market bets:
  - 1X2 recommendation
  - Over/Under 2.5 goals probability (derived from Poisson goal model)
  - Both Teams to Score probability
- Show implied probability vs. what this model suggests (value indicator)

**Share / Export:**
- "Copy Prediction" button (copies formatted summary to clipboard)
- "Export PDF" of the full prediction card

### 4.4 Statistics Hub (`/stats`)

A new page that didn't exist before:

- **League table** (live from API, updated daily)
- **Top scorers** widget
- **Team form heatmap** — a grid of all 20 teams × last 10 matches, coloured W/D/L
- **Home vs Away performance** — horizontal bar chart showing each team's home win rate vs. away win rate

### 4.5 History Page (`/history`) — New Feature

- Store every prediction made (in SQLite, per session or user)
- Show a table: Date | Home | Away | Prediction | Actual Result | ✓/✗
- Running accuracy metric at the top: "Your predictions: 64% accurate"
- This creates engagement and a feedback loop

---

## 5. Backend / ML Logic Revamp

### 5.1 API Structure (FastAPI)

```
GET  /api/fixtures/upcoming        → Next GW fixtures
GET  /api/fixtures/{id}            → Single fixture details
GET  /api/teams                    → All teams + crests
GET  /api/standings                → Current PL table
POST /api/predict                  → Main prediction endpoint
GET  /api/predict/history          → Past predictions (session-based)
GET  /api/stats/form/{team_id}     → Team form last N matches
GET  /api/stats/h2h/{home}/{away}  → Head-to-head history
```

### 5.2 Feature Engineering (Major Improvement)

The current model likely uses raw categorical features. Replace with engineered rolling window features:

**Team form features (rolling 5-match window):**
- `home_wins_last5`, `home_draws_last5`, `home_losses_last5`
- `home_goals_scored_last5`, `home_goals_conceded_last5`
- `home_clean_sheets_last5`
- Same set for away team

**Season context features:**
- `home_position` (current league table rank)
- `away_position`
- `home_points_per_game` (season to date)
- `away_points_per_game`
- `matches_remaining` (proxy for "pressure")

**Head-to-head features:**
- `h2h_home_wins`, `h2h_draws`, `h2h_away_wins` (last 10 meetings)
- `h2h_home_goals_avg`, `h2h_away_goals_avg`

**Referee features:**
- `referee_home_win_rate` (historical, per referee)
- `referee_cards_per_game`

**Match context:**
- `is_weekend` (bool)
- `kickoff_hour` (int, keep but engineer properly)

### 5.3 Model Architecture

Replace single RandomForestClassifier with:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import VotingClassifier
import xgboost as xgb
import lightgbm as lgb

base_models = [
    ('rf',  RandomForestClassifier(n_estimators=300, max_depth=8)),
    ('xgb', xgb.XGBClassifier(n_estimators=200, learning_rate=0.05)),
    ('lgb', lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05)),
]

ensemble = VotingClassifier(
    estimators=base_models,
    voting='soft',          # use probability averaging
    weights=[1, 1.5, 1.5],
)
```

**Target variable:** 3-class (Home Win = 0, Draw = 1, Away Win = 2)

**Train/validation split:** Use time-based split (seasons before current = train, current season = validate). Never use random split for time-series sports data.

**SHAP explainability:**
```python
import shap
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_single_match)
# Return top 5 features by absolute SHAP value to the API
```

### 5.4 Goal Model (New — for Over/Under & BTTS)

Add a separate Poisson regression goal model:

```python
# Fit Dixon-Coles or simple Poisson to predict expected goals
# P(home_goals = k) = Poisson(lambda_home)
# BTTS = P(home_goals >= 1) * P(away_goals >= 1)
# Over 2.5 = P(total_goals > 2.5)
```

This enables the betting insight boxes described in the UI section.

### 5.5 Data Pipeline

```
data/
  raw/
    historical_pl_YYYY-YY.csv   (existing CSVs)
  processed/
    features_engineered.parquet
  cache/
    fixtures_cache.json         (refreshed every 6h via APScheduler)
    standings_cache.json
```

- On startup, check cache age; if stale, refetch from football-data.org
- On prediction request, run feature engineering from cached data + historical data
- Compute SHAP values per request (fast enough for single-match)

---

## 6. Project Structure

```
plbets-v2/
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              ← Home / prediction page
│   │   ├── stats/page.tsx        ← New stats hub
│   │   ├── history/page.tsx      ← New history page
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                   ← Shared primitives (Button, Card, Badge)
│   │   ├── MatchCard.tsx
│   │   ├── PredictionPanel.tsx
│   │   ├── ProbabilityBar.tsx
│   │   ├── ShapChart.tsx
│   │   ├── FormPills.tsx
│   │   ├── H2HTimeline.tsx
│   │   ├── BettingInsightBox.tsx
│   │   └── LeagueTable.tsx
│   ├── lib/
│   │   ├── api.ts                ← API client functions
│   │   └── types.ts
│   ├── public/
│   │   └── team-crests/          ← Cache team logo SVGs
│   ├── tailwind.config.ts
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py               ← FastAPI entry point
│   │   ├── routers/
│   │   │   ├── fixtures.py
│   │   │   ├── predict.py
│   │   │   ├── stats.py
│   │   │   └── history.py
│   │   ├── services/
│   │   │   ├── feature_engineering.py
│   │   │   ├── model.py          ← Ensemble + SHAP
│   │   │   ├── goal_model.py     ← Poisson goal model
│   │   │   ├── data_loader.py
│   │   │   └── football_api.py   ← football-data.org client
│   │   ├── models/
│   │   │   └── schemas.py        ← Pydantic models
│   │   └── db/
│   │       ├── database.py
│   │       └── crud.py
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── cache/
│   ├── ml/
│   │   └── train.py              ← Standalone training script
│   └── requirements.txt
│
├── docker-compose.yml
└── README.md
```

---

## 7. Key New Features Summary

| Feature | Status in v1 | Status in v2 |
|---|---|---|
| Live fixture fetching | ❌ Static dropdowns | ✅ Auto-fetched upcoming GW |
| Team crests/logos | ❌ None | ✅ Displayed throughout |
| Probability visualisation | ❌ None (text only) | ✅ Animated bars + percentages |
| Model explainability | ❌ Black box | ✅ SHAP feature importance chart |
| Head-to-head history | ❌ None | ✅ Last 5 meetings timeline |
| Team form display | ❌ Raw stats in text | ✅ W/D/L pills + rolling stats |
| Goal model (BTTS/O2.5) | ❌ None | ✅ Poisson model |
| Stats hub | ❌ None | ✅ Full page with table, form heatmap |
| Prediction history | ❌ None | ✅ Stored, shown with accuracy |
| Referee data | ❌ Empty dropdown | ✅ Populated + used in model |
| Ensemble ML | ❌ Single RandomForest | ✅ XGB + LGB + RF ensemble |
| Feature engineering | ❌ Raw categoricals | ✅ Rolling window features |
| API framework | Flask (sync) | FastAPI (async, typed) |
| Responsible gambling notice | ❌ None | ✅ Present on all bet-related outputs |

---

## 8. Responsible Gambling Requirement

Every page and component that mentions betting odds, tips, or recommendations **must** include:

```
⚠️ For informational and entertainment purposes only.
   Gambling can be addictive. Please bet responsibly.
   GamStop: gamstop.co.uk | BeGambleAware: begambleaware.org
```

This is non-negotiable. Display it as a subtle footer note beneath any betting-related output.

---

## 9. Environment Variables Needed

```env
# Backend
FOOTBALL_DATA_API_KEY=your_key_here   # free at football-data.org
DATABASE_URL=sqlite:///./plbets.db
CORS_ORIGINS=http://localhost:3000,https://pl-bets.vercel.app

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 10. Suggested Build Order for Claude Code

1. **Scaffold** the full directory structure
2. **Backend first:**
   a. `football_api.py` service + caching
   b. `data_loader.py` with historical CSVs + feature engineering
   c. `model.py` — train ensemble, save as `model.pkl`
   d. `goal_model.py` — Poisson goal model
   e. FastAPI routers: fixtures → predict → stats → history
   f. SQLite schema for prediction history
3. **Frontend:**
   a. Design system (globals.css, CSS variables, font imports)
   b. Shared UI primitives: Button, Card, Badge, Skeleton
   c. Home page layout + sticky nav
   d. MatchCard component + fixture row
   e. PredictionPanel (team picker with crests)
   f. Results components: ProbabilityBar, ShapChart, FormPills, H2HTimeline, BettingInsightBox
   g. Stats page: LeagueTable, FormHeatmap
   h. History page: PredictionTable, AccuracyMetric
4. **Wire up** frontend ↔ backend with SWR hooks
5. **Docker Compose** for local development

---

*Generated by Claude — May 2026. Hand to Claude Code to build.*
