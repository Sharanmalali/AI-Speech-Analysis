# =============================================================================
# AblePro Solutions — Backend image (FastAPI + ML stack)
# Multi-stage build: a builder compiles wheels, the runtime stays lean.
# =============================================================================

# --------------------------------------------------------------------------- #
# Stage 1 — builder
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc g++ git cmake ninja-build \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --wheel-dir=/wheels -r requirements.txt
# --------------------------------------------------------------------------- #
# Stage 2 — runtime
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    HF_HOME=/hf_cache \
    HF_HUB_DISABLE_TELEMETRY=1

# Runtime system libs: ffmpeg (audio decode), libsndfile (soundfile),
# libgomp (numpy/sklearn OpenMP), fonts-noto (Kannada glyphs in PDF reports).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libsndfile1 libgomp1 curl fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Create an unprivileged user.
RUN groupadd -r ablepro && useradd -r -g ablepro -m -d /home/ablepro ablepro

WORKDIR /app

# Install Python deps from pre-built wheels.
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Application code.
COPY . /app

# Storage + model directories (models are mounted/copied at runtime).
# /hf_cache holds the Hugging Face download cache (wav2vec2 gender/age models,
# >1GB) and is backed by a persistent named volume so it survives restarts.
RUN mkdir -p /app/storage/tmp /app/storage/objects /app/storage/reports /models /hf_cache \
    && chown -R ablepro:ablepro /app /models /hf_cache

USER ablepro

EXPOSE 8000

# Container-level healthcheck hitting the liveness probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Gunicorn with Uvicorn workers for production concurrency.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
