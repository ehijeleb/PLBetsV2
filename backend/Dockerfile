# Backend image — FastAPI + ML stack. Multi-stage so the runtime image stays slim.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# libgomp1 is needed by lightgbm/xgboost; libstdc++ is bundled in slim already.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app/ ./app/
COPY ml/ ./ml/
COPY data/ ./data/

# Ensure runtime dirs exist
RUN mkdir -p data/raw data/processed data/cache models_out

EXPOSE 8000

# Render injects $PORT; locally / via docker-compose we fall back to 8000.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fs "http://127.0.0.1:${PORT:-8000}/health" || exit 1

# Fail loudly if model.pkl is missing — it must be committed to the repo (or
# baked into the image at build time) before deploying. Training in production
# is slow and brittle; use the weekly retrain GitHub Action instead.
CMD ["bash", "-lc", "test -f models_out/model.pkl || { echo 'ERROR: models_out/model.pkl missing. Run `python -m ml.train` locally and commit before deploying.' >&2; exit 1; }; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
