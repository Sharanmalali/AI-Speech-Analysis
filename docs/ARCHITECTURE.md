# Architecture

## Overview

AblePro is a production-grade, containerized full-stack application designed for clinical voice analytics. The system is split into:

- **API tier** — Stateless FastAPI application handling REST endpoints
- **Worker tier** — Celery workers for asynchronous ML pipeline processing
- **Frontend tier** — Next.js 15 with React Server Components and App Router
- **Infrastructure** — Redis (broker/cache), PostgreSQL (Supabase), NGINX (reverse proxy)
- **Storage** — Supabase Storage for audio files and generated reports

The architecture prioritizes **scalability**, **security**, and **maintainability** through modular design and container orchestration.

---

## High-Level Architecture Diagram

```
                        ┌─────────────┐
   Browser  ───────────▶│    NGINX    │  reverse proxy (:80)
                        └──────┬──────┘
                  /            │            /api
          ┌───────────────┐    │    ┌──────────────────┐
          │  Next.js 15   │◀───┴───▶│   FastAPI (API)  │
          │  (frontend)   │         └────────┬─────────┘
          │   Port 3000   │                  │ enqueue
          └───────────────┘                  ▼
                                   ┌───────────────────┐
                                   │  Redis (broker +  │
                                   │  result + limits) │
                                   │   Port 6379       │
                                   └─────────┬─────────┘
                                             ▼
                                   ┌───────────────────┐
                                   │  Celery worker    │
                                   │  (ML pipeline)    │
                                   └─────────┬─────────┘
        ┌───────────────┬──────────┬─────────┴───────────┬───────────────┐
        ▼               ▼          ▼                     ▼               ▼
  Diarization    Transcription   Feature           Gender/Age      Atypicality
  (pyannote)     (Whisper)       extraction        (wav2vec2)      (IForest)
                                 (librosa/praat)   (HF Transform)
```

**External Services**:
- Supabase PostgreSQL (persistence)
- Supabase Storage (audio files, PDF reports)
- Hugging Face Hub (model downloads)

---

## Request → Result Lifecycle

### 1. Upload Phase

**Client → API**
```
POST /api/v1/audio/upload (multipart/form-data)
  ↓
- Validate file (extension, MIME type, size, magic bytes)
- Stream to Supabase Storage (or local filesystem in dev)
- Create AudioFile record in database
- Create Job record (status: pending)
- Enqueue Celery task
  ↓
← 202 Accepted { audio_file_id, job_id, status: "pending" }
```

**Rate limiting**: 10 uploads per hour per user (Redis-backed SlowAPI)

### 2. Processing Phase

**Celery Worker**
```
process_audio_job(job_id)
  ↓
1. Update Job.status = "queued"
2. Download audio from storage
3. Run AudioAnalysisPipeline:
   ├─ probe          (duration, sample rate, channels)
   ├─ load           (convert to mono 16kHz WAV)
   ├─ noise_reduce   (optional spectral gating)
   ├─ diarize        (pyannote: who spoke when)
   ├─ transcribe     (Whisper: Kannada speech → text)
   ├─ translate      (Whisper: Kannada → English)
   ├─ segment        (align transcripts to speakers)
   ├─ extract        (acoustic features per segment)
   ├─ predict        (gender, age, atypicality)
   └─ aggregate      (merge into speaker summaries)
4. Write Speaker, Transcription, Prediction records
5. Update Job.status = "completed"
```

**Progress tracking**: After each stage, the worker updates `Job.stage` and `Job.progress` (0-100), allowing the frontend to poll `/jobs/{job_id}/status` for real-time updates.

### 3. Results Phase

**Client → API**
```
GET /api/v1/results/{job_id}
  ↓
- Check Job.status (409 if not completed)
- Query job with speakers, predictions, transcriptions
- Build ResultResponse (nested JSON)
  ↓
← 200 OK { speakers: [...], audio: {...}, has_report: false }
```

**Frontend rendering**:
- Overview tab: Speaking time pie chart, speech/pause bar chart, timeline
- Speakers tab: Individual speaker cards with predictions
- Transcript tab: Bilingual conversation view (Kannada + English)

### 4. Report Generation Phase

**Client → API**
```
POST /api/v1/reports/{job_id}/generate
  ↓
- Build PDF using ReportLab
- Include matplotlib charts (spectrograms, F0 contours)
- Upload PDF to Supabase Storage
- Create Report record
  ↓
← 201 Created

GET /api/v1/reports/{job_id}/download
  ↓
- Generate signed URL from Supabase Storage
- Stream PDF to client
  ↓
← 200 OK (application/pdf)
```

---

## ML Pipeline (Service-Oriented Design)

### Design Principles

**Modular**: Each ML component is independent and replaceable  
**Lazy Loading**: Models load on first use, not at import time  
**Singleton Pattern**: One instance per worker process  
**No Merging**: Models stay separate (never combined into monolithic artifact)

### ML Services Architecture

Location: `backend/app/services/ml/`

```
ml/
├── registry.py              # Model warmup coordinator
├── pipeline.py              # Orchestrates the full workflow
├── types.py                 # Shared data structures
├── speaker_diarization.py   # pyannote.audio
├── transcription.py         # faster-whisper (Whisper wrapper)
├── feature_extraction.py    # librosa + Parselmouth (Praat)
├── gender_age_classifier.py # RandomForest + wav2vec2 fallback
├── hf_gender_age.py         # Hugging Face Transformers (wav2vec2)
├── llm_gender_age.py        # LLM fallback (future)
└── atypicality_classifier.py # IsolationForest + StandardScaler
```

### ML Components Detail

#### 1. Speaker Diarization (`speaker_diarization.py`)

**Model**: `pyannote/speaker-diarization-3.1`  
**Input**: Audio file path  
**Output**: `[(start_time, end_time, speaker_label), ...]`

**Key features**:
- Pre-trained on VoxCeleb and other speaker recognition datasets
- Handles overlapping speech
- Assigns unique labels (SPEAKER_00, SPEAKER_01, etc.)
- Requires `HUGGINGFACE_TOKEN` (gated model)

**Configuration**:
```python
DIARIZATION_DEVICE = "cpu"  # or "cuda" for GPU
```

#### 2. Transcription (`transcription.py`)

**Model**: OpenAI Whisper via `faster-whisper`  
**Input**: Audio segments per speaker  
**Output**: Timestamped transcripts (Kannada + English)

**Process**:
1. Transcribe Kannada speech → Kannada text
2. Translate Kannada → English
3. Align segments by temporal overlap with diarization
4. Assign confidence scores

**Configuration**:
```python
WHISPER_MODEL_SIZE = "small"  # tiny, small, medium, large, large-v3
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"  # int8, float16, float32
```

**Language support**: Primary focus on Kannada (kn) → English (en) translation

#### 3. Feature Extraction (`feature_extraction.py`)

**Libraries**: librosa (spectral features), Parselmouth (acoustic features)  
**Input**: Audio segment per speaker  
**Output**: Two feature sets

**Atypicality features (7 dimensions)**:
1. `latency_to_speak_sec` — Delay before first utterance
2. `pause_to_speech_ratio` — Pause duration / speech duration
3. `pronunciation_flux_var` — Variance in pronunciation patterns
4. `f0_mean` — Mean fundamental frequency (pitch)
5. `jitter` — Pitch perturbation (vocal cord irregularity)
6. `shimmer` — Amplitude perturbation (voice tremor)
7. `hnr` — Harmonics-to-Noise Ratio (voice quality)

**Gender/Age features (483 dimensions)**:
- Log-mel spectrogram summary (480 features)
- Statistical aggregates (mean, std, percentiles)

**Clinical relevance**: Jitter, shimmer, and HNR are established biomarkers for vocal pathology and neurological conditions.

#### 4. Gender & Age Classification (`gender_age_classifier.py`, `hf_gender_age.py`)

**Primary**: RandomForest trained on acoustic features  
**Fallback**: Hugging Face wav2vec2 models

**Models**:
- Gender: `alefiury/wav2vec2-large-xlsr-53-gender-recognition-librispeech`
- Age: `alefiury/wav2vec2-xls-r-300m-adult-child-cls`

**Prediction strategy**:
```python
if random_forest_has_classes:
    return random_forest.predict(features)
else:
    return hf_transformer.predict(audio)
```

**Note**: Current `gender_age_clf.pkl` was trained on single-class data (all class 0), so predictions default to "unknown". Replace with properly trained model for real classifications.

#### 5. Atypicality Classification (`atypicality_classifier.py`)

**Model**: IsolationForest (unsupervised anomaly detection)  
**Input**: 7 scaled acoustic features  
**Output**: `typical` or `atypical` + confidence score

**Process**:
1. StandardScaler normalizes features
2. IsolationForest computes anomaly score
3. Score < 0 → `typical`, Score > 0 → `atypical`
4. Confidence derived from distance from decision boundary

**Configuration**:
```python
N_ESTIMATORS = 200
CONTAMINATION = 0.1  # Expected proportion of outliers
```

**Clinical interpretation**: Atypical scores flag speakers for manual review by clinicians.

### Model Warmup Strategy

**Location**: `backend/app/main.py` → `lifespan()` → `warmup_models()`

**Process**:
```python
async def lifespan(app: FastAPI):
    # Warm models on startup
    try:
        from app.services.ml.registry import warmup_models
        warmup_models()
    except Exception as exc:
        logger.warning("model_warmup_skipped", error=str(exc))
    
    yield
    
    # Cleanup on shutdown
    logger.info("shutdown", app=settings.APP_NAME)
```

**Benefits**:
- First request has no cold-start delay
- All models loaded into memory before serving traffic
- Graceful degradation if models unavailable (API still boots)

**Docker optimization**: Models cached in persistent volume to avoid re-downloading on container restart.

---

## Data Model (PostgreSQL)

### Entity-Relationship Diagram

```
users
  ├─1:N─→ audio_files
  │         ├─1:N─→ jobs
  │         │        ├─1:N─→ speakers
  │         │        │         ├─1:N─→ transcriptions
  │         │        │         └─1:1─→ predictions
  │         │        └─1:1─→ reports
  │         └─ (uploaded audio metadata)
  └─1:N─→ audit_logs
```

### Core Tables

**users**
- `id` (UUID, PK)
- `email` (unique, indexed)
- `hashed_password` (bcrypt)
- `role` (enum: admin, doctor, user)
- `is_active`, `is_verified` (booleans)
- Timestamps: `created_at`, `updated_at`

**audio_files**
- `id` (UUID, PK)
- `user_id` (FK → users)
- `original_filename`, `content_type`, `extension`
- `storage_path` (Supabase or local)
- `size_bytes`, `duration_seconds`, `sample_rate`, `channels`
- Timestamps

**jobs**
- `id` (UUID, PK)
- `audio_file_id` (FK → audio_files)
- `status` (enum: pending, queued, processing, completed, failed, cancelled)
- `stage` (enum: uploaded, diarization, transcription, etc.)
- `progress` (0-100)
- `detected_speakers`, `processing_time_seconds`
- `error_message` (nullable)
- Timestamps: `started_at`, `finished_at`

**speakers**
- `id` (UUID, PK)
- `job_id` (FK → jobs)
- `label` (SPEAKER_00, SPEAKER_01, etc.)
- `diarization_id` (pyannote identifier)
- `color` (hex, for UI)
- `total_speech_seconds`, `total_pause_seconds`
- `segment_count`, `word_count`

**transcriptions**
- `id` (UUID, PK)
- `speaker_id` (FK → speakers)
- `start_time`, `end_time` (float, seconds)
- `text_source` (Kannada)
- `text_translated` (English)
- `confidence` (0.0-1.0)

**predictions**
- `speaker_id` (FK → speakers, PK)
- `gender` (enum: male, female, unknown)
- `gender_confidence` (0.0-1.0)
- `age_group` (enum: child, teen, adult, senior, unknown)
- `age_confidence` (0.0-1.0)
- `gender_age_source` (model, hf, llm)
- `atypicality` (enum: typical, atypical, unknown)
- `atypicality_score` (float)
- `atypicality_confidence` (0.0-1.0)
- `features` (JSONB: acoustic feature snapshot)

**reports**
- `id` (UUID, PK)
- `job_id` (FK → jobs, unique)
- `storage_path` (PDF location)
- `generated_at`

**audit_logs** (append-only)
- `id` (UUID, PK)
- `user_id` (FK → users, nullable)
- `action` (enum: LOGIN, UPLOAD, VIEW_RESULT, etc.)
- `resource_type`, `resource_id`
- `ip_address`, `user_agent`
- `details` (JSONB)
- `created_at`

### Indexes

- `users.email` (unique, btree)
- `jobs.audio_file_id` (btree)
- `jobs.status` (btree, for filtering)
- `speakers.job_id` (btree)
- `transcriptions.speaker_id` (btree)
- `audit_logs.user_id, created_at` (composite, for user history)

---

## Security Architecture

### Authentication Flow

**Registration/Login**:
```
1. Client → POST /auth/register or /login
2. API validates credentials (bcrypt for password)
3. API generates:
   - Access token (JWT, 30 min expiry, in response body)
   - Refresh token (JWT, 7 days expiry, HttpOnly cookie)
4. Client stores access token in memory
5. Client includes "Authorization: Bearer {access_token}" in requests
```

**Token Refresh**:
```
1. Access token expires
2. API returns 401 Unauthorized
3. Client → POST /auth/refresh (with refresh cookie)
4. API validates refresh token, issues new access token
5. Client retries original request with new token
```

**Logout**:
```
1. Client → POST /auth/logout
2. API clears refresh cookie
3. Client discards access token
```

### Authorization (RBAC)

**Roles**:
- `user`: Can upload files, view own results
- `doctor`: Can view all results (for clinical review)
- `admin`: Full access (user management, audit logs)

**Implementation**: `require_roles()` FastAPI dependency

```python
@router.get("/admin/users")
async def list_users(
    user: User = Depends(require_roles(["admin"]))
):
    ...
```

**Resource ownership**: Jobs scoped to creating user (except admin/doctor)

### Security Hardening

**Upload validation**:
1. File extension check (`.wav`, `.mp3`, etc.)
2. MIME type verification (`audio/wav`, `audio/mpeg`, etc.)
3. Size limit (configurable, default 100MB)
4. Magic byte detection (actual file type)
5. Malformed audio rejection (probe with ffmpeg)

**Rate limiting** (SlowAPI + Redis):
- `/auth/login`: 5 requests/minute
- `/auth/register`: 3 requests/minute
- `/audio/upload`: 10 requests/hour

**CORS**: Configurable allow-list (`CORS_ORIGINS` env var)

**Containers**: Non-root user, health checks, read-only root filesystem where possible

**Secrets**: Environment variables only, never in source code

**Audit trail**: All sensitive operations logged (who, what, when, where)

---

## Frontend Architecture (Next.js 15)

### App Router Structure

```
src/app/
├── layout.tsx                 # Root layout (providers, fonts)
├── page.tsx                   # Landing page (marketing)
├── (auth)/                    # Auth route group
│   ├── login/
│   └── register/
├── dashboard/                 # Protected routes
│   ├── layout.tsx             # AuthGuard wrapper
│   ├── page.tsx               # Dashboard home
│   ├── upload/
│   ├── processing/[jobId]/
│   └── results/[jobId]/
└── demo/                      # Public demo (NO AUTH)
    ├── layout.tsx             # Custom layout (no AuthGuard)
    └── page.tsx               # Demo results page
```

**Key difference**: `/demo` is a **top-level route** outside `/dashboard`, bypassing authentication. This allows judges and stakeholders to instantly view a complete analysis.

### Component Architecture

```
components/
├── ui/                        # Shadcn/ui primitives
│   ├── button.tsx
│   ├── card.tsx
│   ├── tabs.tsx
│   └── ...
├── dashboard/                 # Dashboard-specific
│   ├── sidebar.tsx
│   ├── topbar.tsx
│   ├── stat-card.tsx
│   └── page-header.tsx
├── results/                   # Analysis visualization
│   ├── charts.tsx             # Pie + bar charts (Recharts)
│   ├── timeline.tsx           # Speaker timeline
│   ├── speaker-card.tsx       # Individual speaker details
│   └── transcript.tsx         # Bilingual conversation view
├── auth/
│   └── auth-guard.tsx         # Protected route wrapper
├── marketing/
│   ├── navbar.tsx
│   ├── footer.tsx
│   └── hero-scene.tsx         # 3D animation
└── motion/
    ├── reveal.tsx             # Scroll animations
    └── counter.tsx            # Animated numbers
```

### State Management

**Zustand** (`lib/store/auth-store.ts`):
```typescript
interface AuthState {
  accessToken: string | null;
  setAccessToken: (token: string | null) => void;
  clear: () => void;
}
```

**React Query** (`@tanstack/react-query`):
- Server state caching
- Automatic refetching
- Optimistic updates
- Background synchronization

**Example usage**:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['results', jobId],
  queryFn: () => resultService.get(jobId),
});
```

### API Client (`lib/services.ts`)

Axios-based typed client with automatic token injection and refresh:

```typescript
// Interceptor adds Authorization header
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor handles 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return api(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

---

## Demo Mode Architecture

### Purpose

Provide instant, no-authentication access to a complete analysis result for:
- Hackathon judges (limited demo time)
- Stakeholder presentations
- Quick product previews
- Public showcases

### Implementation

**Backend** (`backend/app/routers/demo.py`):
```python
# Static JSON file with pre-computed results
DEMO_DATA_PATH = Path(__file__).parent / "demo_data.json"

@router.get("/sample-result", response_model=ResultResponse)
async def get_demo_results() -> ResultResponse:
    # Load from cached JSON (not live ML processing)
    return load_demo_data()
```

**Data generation** (`backend/generate_demo_data.py`):
```bash
# One-time process to create demo data
python backend/generate_demo_data.py

# Processes Sample1C.wav through full ML pipeline
# Saves results to demo_data.json
# Subsequent requests load from JSON (< 5ms response time)
```

**Frontend** (`frontend/src/app/demo/page.tsx`):
- Standalone page with no authentication
- Custom layout (no sidebar, no user profile)
- "Demo Mode" banner to indicate sample data
- Full result visualization (charts, speakers, transcript)
- "Back to Home" navigation

**Route isolation**:
```
/dashboard/*     → Requires AuthGuard
/demo            → Public access (no AuthGuard)
/                → Public marketing page
```

### Benefits

✅ **Instant loading**: No ML processing, just JSON parsing  
✅ **No failures**: Pre-computed data never errors  
✅ **Scalable**: Handles unlimited traffic (static data)  
✅ **Authentic**: Real ML output, not fake mock data

---

## Scaling Considerations

### Horizontal Scaling

**API tier**:
- Stateless design allows N replicas behind NGINX
- Session state in JWT + Redis (no server affinity needed)
- Load balancing: round-robin or least-connections

**Worker tier**:
- Celery concurrency: `--concurrency=4` (or auto-scale based on CPU)
- Multiple worker containers for parallel job processing
- Task routing by queue (e.g., separate queue for urgent jobs)

**Database**:
- Supabase handles replication and read replicas
- Connection pooling via PgBouncer
- Read-heavy queries use replicas

**Redis**:
- Redis Cluster for high availability
- Sentinel for automatic failover
- Separate instances for broker vs. cache vs. rate-limiting

### Vertical Scaling

**GPU acceleration**:
```python
# Enable GPU for heavy models
DIARIZATION_DEVICE = "cuda"
WHISPER_DEVICE = "cuda"
```

**Resource allocation**:
- API: 1 CPU, 1GB RAM per replica
- Worker: 2-4 CPU, 4-8GB RAM (depends on model size)
- Redis: 2GB RAM minimum
- PostgreSQL: Depends on data volume

### Caching Strategy

**Model caching**:
- Docker volume for Hugging Face cache
- Prevents re-downloading 1.5GB+ on restart
- Mounted at `/root/.cache/huggingface`

**Result caching**:
- Redis caches completed job results
- TTL: 1 hour (configurable)
- Reduces database load for repeated queries

**Frontend caching**:
- Next.js static generation for marketing pages
- React Query caching for API responses
- Service Worker for offline support (future)

---

## Deployment

### Docker Compose (Production)

```bash
docker compose up -d --build
```

**Services**:
- `backend`: FastAPI (Gunicorn + Uvicorn workers)
- `frontend`: Next.js (standalone mode)
- `celery`: Celery worker
- `redis`: Redis server
- `nginx`: Reverse proxy

**Volumes**:
- `postgres_data`: Database persistence
- `redis_data`: Redis persistence
- `hf_cache`: Hugging Face model cache
- `uploads`: Audio file storage (if not using Supabase)

**Networks**:
- `ablepro-network`: Internal container communication

### Environment Configuration

**Production** (`.env`):
```env
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@host:5432/ablepro
SUPABASE_URL=https://xxx.supabase.co
HUGGINGFACE_TOKEN=hf_xxx
CORS_ORIGINS=https://ablepro.com
```

**Development** (`docker-compose.dev.yml`):
```yaml
services:
  backend:
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app  # Hot reload
  frontend:
    command: npm run dev
    volumes:
      - ./frontend:/app  # Hot reload
```

---

## Monitoring & Observability

### Health Checks

**Liveness**: `/health` (process alive?)  
**Readiness**: `/ready` (dependencies healthy?)

**Docker health check**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
```

### Logging

**Structured logging** (JSON format):
```python
logger.info("job_started", job_id=str(job_id), user_id=str(user_id))
logger.error("model_failed", model="diarization", error=str(exc))
```

**Log aggregation**: Compatible with ELK stack, Datadog, CloudWatch

### Metrics (Future)

- Request count, latency (Prometheus)
- Job processing time distribution
- Model inference time per stage
- Error rates by endpoint
- Active users, concurrent jobs

---

## Future Enhancements

### Planned Features

1. **Real-time WebSocket updates**: Replace polling with WebSocket job status
2. **Batch processing**: Upload and process multiple files at once
3. **Custom model training**: Allow users to fine-tune models
4. **Multi-language support**: Beyond Kannada (Hindi, Tamil, Telugu)
5. **Speaker identification**: Name speakers (not just SPEAKER_01)
6. **Emotion detection**: Classify emotional states from speech
7. **Video support**: Extract audio from video files
8. **API webhooks**: Notify external systems on job completion

### Technical Debt

- Replace current `gender_age_clf.pkl` with properly trained model
- Add comprehensive integration tests
- Implement circuit breakers for external services
- Add request tracing (OpenTelemetry)
- Optimize Docker image sizes (multi-stage builds)

---

## Appendix: Technology Choices

### Why FastAPI?
- **Performance**: Async/await, Starlette, Pydantic
- **Type safety**: Automatic validation, OpenAPI docs
- **Ecosystem**: Rich middleware, dependency injection

### Why Celery?
- **Maturity**: Battle-tested in production
- **Flexibility**: Multiple brokers (Redis, RabbitMQ)
- **Monitoring**: Flower dashboard, Celery events

### Why Next.js 15?
- **Developer experience**: App Router, Server Components
- **Performance**: Automatic code splitting, image optimization
- **SEO**: Server-side rendering, static generation

### Why Supabase?
- **Simplicity**: Managed Postgres, auth, storage in one
- **Scalability**: Auto-scaling, backups, point-in-time recovery
- **Developer tools**: Realtime subscriptions, REST API

### Why Docker?
- **Consistency**: Same environment dev → prod
- **Isolation**: Models, dependencies contained
- **Scalability**: Orchestrate with Kubernetes (future)

---

**Document Version**: 2.0  
**Last Updated**: December 2024  
**Maintainer**: AblePro Solutions Team
