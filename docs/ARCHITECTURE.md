# Architecture

## Overview

AblePro is split into a stateless **API tier** (FastAPI), an asynchronous
**worker tier** (Celery) for the long-running ML pipeline, a **frontend**
(Next.js), and shared infrastructure (Redis, Supabase Postgres + Storage),
fronted by **NGINX**.

## Request → result lifecycle

1. **Upload** — `POST /api/v1/audio/upload`. The file is validated
   (extension, MIME, size, magic bytes), streamed to object storage, and an
   `AudioFile` + `Job` (status `pending`) are persisted. A Celery task is
   enqueued and the API returns `202 Accepted` immediately.
2. **Processing** — the `process_audio_job` worker task downloads the audio
   and runs `AudioAnalysisPipeline`, writing `stage`/`progress` updates to the
   `Job` row after each phase (so the UI can poll `/jobs/{id}/status`).
3. **Pipeline phases** — probe → load → noise reduction → diarization
   (pyannote) → transcription + translation (Whisper) → segment-to-speaker
   assignment → per-speaker feature extraction → gender/age + atypicality
   inference → aggregation.
4. **Persistence** — `Speaker`, `Transcription` and `Prediction` rows are
   written; the `Job` becomes `completed`.
5. **Results** — `GET /api/v1/results/{job_id}` returns the full payload; the
   dashboard renders charts, a timeline and the transcript.
6. **Report** — `POST /reports/{job_id}/generate` builds a PDF (ReportLab +
   matplotlib charts) stored in object storage; `GET …/download` streams it.

## ML layer (service-oriented)

Each model is wrapped in its own module under `app/services/ml/` and exposed as
a lazily-initialised process-wide singleton:

- `speaker_diarization.py` — pyannote pipeline (gated; needs `HUGGINGFACE_TOKEN`).
- `transcription.py` — faster-whisper; runs `transcribe` (Kannada) and
  `translate` (English) and aligns segments by temporal overlap.
- `feature_extraction.py` — librosa + Praat/parselmouth; emits the 7 atypicality
  features and the 480-dim gender/age vector.
- `gender_age_classifier.py` — RandomForest; runtime `classes_` + label map.
- `atypicality_classifier.py` — StandardScaler + IsolationForest.

`registry.warmup_models()` initialises them once at startup; `pipeline.py`
orchestrates them but holds no model state itself. Models are loaded exactly
once and never merged into a single artifact.

## Data model

`users 1─* audio_files 1─* jobs 1─* speakers 1─* transcriptions`, plus
`speakers 1─1 predictions`, `jobs 1─1 reports`, and an append-only
`audit_logs` table. UUID primary keys, timezone-aware timestamps, JSONB columns
for acoustic feature snapshots and audit detail (on Postgres).

## Security model

- **AuthN**: JWT access tokens (Bearer) + refresh tokens (HttpOnly cookie).
  Supabase social/email login is exchanged for an AblePro session via
  `/auth/supabase`.
- **AuthZ**: `UserRole` ∈ {admin, doctor, user}; `require_roles` dependency;
  job access scoped to owner (admins/doctors see all).
- **Hardening**: SlowAPI rate limits (Redis-backed), upload validation,
  structured audit trail, CORS allow-list, non-root containers, healthchecks.

## Scaling notes

- The API is stateless and horizontally scalable behind NGINX.
- Workers scale independently; concurrency is tuned via `--concurrency`.
- Redis is the shared broker, result backend and rate-limit store.
- Model warmup happens per-worker; for GPU inference set `*_DEVICE=cuda`.
