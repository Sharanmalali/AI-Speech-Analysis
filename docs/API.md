# API Reference

Base path: `/api/v1`. Interactive docs: `/docs` (Swagger UI), `/redoc`,
machine spec at `/openapi.json`.

All errors share a consistent envelope:

```json
{ "error": { "code": "machine_code", "message": "Human readable", "details": {} } }
```

Authenticate by sending `Authorization: Bearer <access_token>`. The refresh
token is delivered/consumed via the `ablepro_refresh` HttpOnly cookie.

---

## Authentication

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/auth/register` | Create a local account → `{ user, tokens }` (201) | ❌ |
| POST | `/auth/login` | Email + password → `{ user, tokens }` | ❌ |
| POST | `/auth/supabase` | Exchange a Supabase token for an AblePro session | ❌ |
| POST | `/auth/refresh` | New access token from the refresh cookie | ❌ |
| POST | `/auth/logout` | Clear the refresh cookie | ✅ |
| GET  | `/auth/me` | Current user profile | ✅ |

**Example — register**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"doc@clinic.org","password":"Sup3rSecret!","full_name":"Dr Doe"}'
```

**Response (201)**
```json
{
  "user": {
    "id": "uuid",
    "email": "doc@clinic.org",
    "full_name": "Dr Doe",
    "role": "user",
    "is_active": true,
    "is_verified": false
  },
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

---

## Audio & Jobs

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/audio/upload` | Multipart upload → `202 { audio_file_id, job_id, status }` | ✅ (rate-limited) |
| GET  | `/audio/{audio_file_id}/stream` | Stream the audio file | ✅ (owner/privileged) |
| GET  | `/jobs` | Paginated job list (`?page=&page_size=`) | ✅ |
| GET  | `/jobs/{job_id}` | Job detail with audio metadata | ✅ |
| GET  | `/jobs/{job_id}/status` | Poll `{ status, stage, progress }` | ✅ |
| POST | `/jobs/{job_id}/cancel` | Cancel a pending/running job | ✅ |
| DELETE | `/jobs/{job_id}` | Delete a job and its associated data | ✅ |

**Example — upload**
```bash
curl -X POST http://localhost:8000/api/v1/audio/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@conversation.wav;type=audio/wav'
```

**Upload response (202)**
```json
{
  "audio_file_id": "uuid",
  "job_id": "uuid",
  "status": "pending",
  "message": "Audio uploaded successfully. Processing started."
}
```

**Allowed file types**: `wav, mp3, aac, ogg, m4a, flac`  
**Max size**: 100 MB (configurable via `MAX_UPLOAD_SIZE_MB`)

**Job status response**
```json
{
  "id": "uuid",
  "status": "processing",
  "stage": "transcription",
  "progress": 45,
  "detected_speakers": 3,
  "error_message": null
}
```

**Job statuses**: `pending`, `queued`, `processing`, `completed`, `failed`, `cancelled`

**Pipeline stages**: `uploaded`, `noise_reduction`, `diarization`, `segmentation`, `transcription`, `translation`, `feature_extraction`, `gender_prediction`, `age_prediction`, `atypicality_classification`, `aggregation`, `report_generation`, `done`

---

## Results & Reports

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET  | `/results/{job_id}` | Full analysis (409 until job `completed`) | ✅ |
| POST | `/reports/{job_id}/generate` | Build the PDF report | ✅ |
| GET  | `/reports/{job_id}/download` | Download the PDF (`application/pdf`) | ✅ |

**`/results/{job_id}` (200) response**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "detected_speakers": 3,
  "language_source": "kn",
  "language_target": "en",
  "processing_time_seconds": 127.5,
  "audio": {
    "original_filename": "conversation.wav",
    "duration_seconds": 180.3,
    "sample_rate": 16000,
    "channels": 1
  },
  "speakers": [
    {
      "id": "uuid",
      "label": "SPEAKER_01",
      "diarization_id": "diar-001",
      "color": "#3B82F6",
      "total_speech_seconds": 62.4,
      "total_pause_seconds": 12.8,
      "segment_count": 8,
      "word_count": 245,
      "prediction": {
        "gender": "male",
        "gender_confidence": 0.87,
        "age_group": "adult",
        "age_confidence": 0.82,
        "raw_class_label": "0",
        "gender_age_source": "model",
        "atypicality": "typical",
        "atypicality_score": -0.15,
        "atypicality_confidence": 0.89,
        "features": {
          "latency_to_speak_sec": 0.52,
          "pause_to_speech_ratio": 0.21,
          "pronunciation_flux_var": 0.09,
          "f0_mean": 138.7,
          "jitter": 0.014,
          "shimmer": 0.048,
          "hnr": 17.8
        }
      },
      "transcriptions": [
        {
          "id": "uuid",
          "start_time": 2.4,
          "end_time": 9.8,
          "text_source": "ನಮಸ್ಕಾರ, ಇಂದು ನಾವು ಮಾನಸಿಕ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ಚರ್ಚಿಸೋಣ",
          "text_translated": "Hello, today let's discuss mental health",
          "confidence": 0.92
        }
      ]
    }
  ],
  "has_report": false
}
```

**Error when results not ready (409)**
```json
{
  "error": {
    "code": "results_not_ready",
    "message": "Results are not ready (job status: processing).",
    "details": {
      "status": "processing",
      "progress": 65
    }
  }
}
```

---

## Demo (Public Access)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/demo/sample-result` | Get pre-loaded demo analysis results | ❌ |

**Purpose**: Provides instant access to a complete analysis result for demonstrations, hackathon judges, or quick product previews without requiring authentication or file upload.

**`/demo/sample-result` (200) response**

Returns the same structure as `/results/{job_id}` but with pre-computed data from a sample audio file. The data is cached in memory for instant response times (< 5ms).

**Example**
```bash
curl http://localhost:8000/api/v1/demo/sample-result
```

**Features**:
- ✅ No authentication required
- ✅ Instant response (pre-computed, cached)
- ✅ Real analysis data (not fake/mock)
- ✅ Full result structure (speakers, transcriptions, predictions)
- ✅ Perfect for demos and stakeholder presentations

**Error when demo data not available (503)**
```json
{
  "error": {
    "code": "demo_data_not_available",
    "message": "Demo data has not been generated yet. Please contact support.",
    "details": {
      "info": "Run 'python backend/generate_demo_data.py' to create demo data"
    }
  }
}
```

---

## Admin (role: admin)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET   | `/admin/users` | Paginated user list | ✅ (admin) |
| PATCH | `/admin/users/{id}/role` | Change a user's role | ✅ (admin) |
| PATCH | `/admin/users/{id}/deactivate` | Disable an account | ✅ (admin) |
| GET   | `/admin/audit-logs` | Paginated audit trail | ✅ (admin) |

**Example — list users**
```bash
curl http://localhost:8000/api/v1/admin/users?page=1&page_size=20 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response**
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "user",
      "is_active": true,
      "is_verified": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

## Health & Monitoring

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/health` | Liveness probe | ❌ |
| GET | `/ready` | Readiness probe (checks database) | ❌ |

**`/health` response (200)**
```json
{
  "status": "ok",
  "app": "AblePro Solutions",
  "version": "1.0.0",
  "environment": "production"
}
```

**`/ready` response (200)**
```json
{
  "status": "ok",
  "checks": {
    "database": "ok"
  }
}
```

**`/ready` degraded response (200)**
```json
{
  "status": "degraded",
  "checks": {
    "database": "unavailable"
  }
}
```

---

## Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | OK | Successful request |
| `201` | Created | Resource created (e.g., registration) |
| `202` | Accepted | Async operation started (e.g., upload) |
| `400` | Bad Request | Invalid file format, malformed data |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Results not ready, resource state conflict |
| `422` | Unprocessable Entity | Validation error (Pydantic) |
| `429` | Too Many Requests | Rate limit exceeded |
| `503` | Service Unavailable | Demo data missing, service degraded |
| `5xx` | Server Error | Internal server error |

---

## Rate Limiting

Endpoints with rate limits (backed by Redis):

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 5 requests | per minute |
| `/auth/register` | 3 requests | per minute |
| `/audio/upload` | 10 requests | per hour |

**Rate limit response (429)**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded",
    "details": {
      "limit": "5 per 1 minute"
    }
  }
}
```

**Headers**:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Pagination

List endpoints support pagination via query parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `page` | Page number (1-indexed) | 1 |
| `page_size` | Items per page | 20 |

**Response structure**
```json
{
  "items": [...],
  "total": 100,
  "page": 2,
  "page_size": 20
}
```

---

## Frontend Integration

The Next.js frontend includes a type-safe API client at `frontend/src/lib/services.ts` with methods for all endpoints:

- `authService.login()`, `authService.register()`, `authService.logout()`
- `uploadService.upload()`, `uploadService.streamUrl()`
- `jobService.list()`, `jobService.status()`, `jobService.cancel()`
- `resultService.get()`
- `reportService.download()`
- `demoService.getSampleResult()` *(new)*

All methods return typed promises using the schemas defined in `frontend/src/lib/types.ts`.

---

## WebSocket Support (Future)

Real-time job status updates will be available via WebSocket connections at `/ws/jobs/{job_id}`. Currently, clients should poll `/jobs/{job_id}/status` every 2-5 seconds.
