# AblePro Solutions

**AI-Powered Multi-speaker Mental Health Audio Analytics Platform**

AblePro ingests a conversation recording and produces an end-to-end analysis:
speaker diarization, Kannada→English transcription with timestamps, per-speaker
gender & age-group estimation, and typical/atypical speech screening — surfaced
in an interactive dashboard and a downloadable PDF report.

---

## Architecture

```
                        ┌─────────────┐
   Browser  ───────────▶│    NGINX    │  reverse proxy (:80)
                        └──────┬──────┘
                  /            │            /api
          ┌───────────────┐    │    ┌──────────────────┐
          │  Next.js 15   │◀───┴───▶│   FastAPI (API)  │
          │  (frontend)   │         └────────┬─────────┘
          └───────────────┘                  │ enqueue
                                             ▼
                                   ┌───────────────────┐
                                   │  Redis (broker +  │
                                   │  result + limits) │
                                   └─────────┬─────────┘
                                             ▼
                                   ┌───────────────────┐
                                   │  Celery worker    │
                                   │  (ML pipeline)    │
                                   └─────────┬─────────┘
        ┌───────────────┬──────────┬─────────┴───────────┬───────────────┐
        ▼               ▼          ▼                     ▼               ▼
  Diarization    Transcription   Feature           Gender/Age      Atypicality
  (pyannote)     (Whisper)       extraction        (RandomForest)  (IForest)
                                 (librosa/praat)
```

Persistence is **Supabase PostgreSQL**; uploaded audio and generated reports
live in **Supabase Storage** (with a local-filesystem fallback for dev).

The ML layer is **service-oriented**: each model is an independent, lazily
loaded singleton. They are never merged into one artifact and are warmed once
at worker startup.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and
[`docs/API.md`](docs/API.md) for details.

---

## Repository layout

```
.
├── backend/            FastAPI app, ML services, Celery tasks, tests
│   ├── app/
│   │   ├── config/     Pydantic settings
│   │   ├── core/       logging, security (JWT/bcrypt), exceptions, rate limit
│   │   ├── database/   SQLAlchemy engine, base, init
│   │   ├── models/     ORM models (users, jobs, speakers, …)
│   │   ├── schemas/    Pydantic request/response models
│   │   ├── routers/    auth, audio, jobs, results, reports, admin, health
│   │   ├── services/   ml/ (diarization, transcription, classifiers,
│   │   │               feature_extraction, pipeline, registry),
│   │   │               storage, report_generator, job_service, auth_service
│   │   ├── tasks/       Celery app + pipeline task + dispatch
│   │   └── utils/       audio, files, timestamp helpers
│   ├── alembic/         migrations
│   └── tests/           pytest suite
├── frontend/            Next.js 15 (App Router, TS, Tailwind, shadcn-style UI)
├── docker/nginx/        reverse-proxy config
├── models/              the three pre-trained .pkl artifacts
├── docs/                architecture & API docs
├── docker-compose.yml          production stack
└── docker-compose.dev.yml      dev overrides (hot reload)
```

---

## The ML models

Three pre-trained artifacts in `models/` are loaded **as-is** (never retrained):

| File | Type | Inputs |
|------|------|--------|
| `atypicality_scaler.pkl` | `StandardScaler` | 7 acoustic features |
| `atypicality_iforest.pkl` | `IsolationForest` (200 trees) | the scaled 7 features |
| `gender_age_clf.pkl` | `RandomForestClassifier` | 483 features |

The 7 atypicality features (fixed order): `latency_to_speak_sec`,
`pause_to_speech_ratio`, `pronunciation_flux_var`, `f0_mean`, `jitter`,
`shimmer`, `hnr`.

> **⚠️ Important model caveat.** The supplied `gender_age_clf.pkl` was trained
> on data containing a **single class** (`classes_ == [0]`), so it always
> predicts `0` and gender/age are reported as **"unknown"**. The service reads
> `model.classes_` at runtime and maps labels via a configurable table, so
> dropping in a properly-trained multi-class model requires **no code change**.
> The 480 numeric features have no recoverable names in the pickle; we feed a
> documented, deterministic log-mel summary (`feature_extraction.py`). Align
> that function with your original training pipeline for meaningful output.

---

## Quick start (Docker)

```bash
# 1. Configure secrets
cp backend/.env.example backend/.env
#    Edit backend/.env: set JWT_SECRET_KEY, DATABASE_URL (Supabase),
#    SUPABASE_* keys and HUGGINGFACE_TOKEN (for pyannote diarization).

# 2. Production stack (NGINX on :80)
docker compose up -d --build

# 3. Development stack (hot reload; API :8000, web :3000, flower :5555)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Open http://localhost (prod) or http://localhost:3000 (dev). API docs at
`/docs` (Swagger) and `/redoc`.

---

## Local development (without Docker)

**Backend**
```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
# System deps: ffmpeg, libsndfile  (brew install ffmpeg libsndfile)
cp .env.example .env            # works out-of-the-box on SQLite
uvicorn app.main:app --reload   # http://localhost:8000/docs
# Worker (separate shell, needs Redis running):
celery -A app.tasks.celery_app worker --loglevel=info
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                     # http://localhost:3000
```

---

## Configuration

All backend settings come from environment variables — see
[`backend/.env.example`](backend/.env.example). Key ones:

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | Signs access/refresh tokens (**required** in prod) |
| `DATABASE_URL` | Supabase Postgres connection string (SQLite if unset) |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | Storage + auth provisioning |
| `SUPABASE_JWT_SECRET` | Validates Supabase social-login tokens |
| `HUGGINGFACE_TOKEN` | Required to load the gated pyannote pipeline |
| `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Queue/cache |
| `WHISPER_MODEL_SIZE` | `tiny`…`large-v3` (default `small`) |
| `MAX_UPLOAD_SIZE_MB` | Upload ceiling (default 100) |

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest               # unit + integration + ml-artifact tests
```

The suite is hermetic: SQLite, local storage and a stubbed task queue — no
external services required.

---

## Security

JWT auth with refresh-token rotation (HttpOnly cookie), RBAC (admin / doctor /
user), SlowAPI + Redis rate limiting, strict upload validation (extension,
content-type, size, magic-byte sniff), audit trails, secure cookies, CORS
allow-listing, and non-root containers with healthchecks. Network-exposed
endpoints require authentication; the upload and auth endpoints are additionally
rate-limited.
