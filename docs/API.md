# API Reference

Base path: `/api/v1`. Interactive docs: `/docs` (Swagger UI), `/redoc`,
machine spec at `/openapi.json`.

All errors share a consistent envelope:

```json
{ "error": { "code": "machine_code", "message": "Human readable", "details": {} } }
```

Authenticate by sending `Authorization: Bearer <access_token>`. The refresh
token is delivered/consumed via the `ablepro_refresh` HttpOnly cookie.

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create a local account → `{ user, tokens }` (201) |
| POST | `/auth/login` | Email + password → `{ user, tokens }` |
| POST | `/auth/supabase` | Exchange a Supabase token for an AblePro session |
| POST | `/auth/refresh` | New access token from the refresh cookie |
| POST | `/auth/logout` | Clear the refresh cookie (auth required) |
| GET  | `/auth/me` | Current user profile (auth required) |

**Example — register**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"doc@clinic.org","password":"Sup3rSecret!","full_name":"Dr Doe"}'
```

## Audio & jobs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/audio/upload` | Multipart upload → `202 { audio_file_id, job_id, status }` (rate-limited) |
| GET  | `/audio/{audio_file_id}/stream` | Stream the audio (owner/privileged) |
| GET  | `/jobs` | Paginated job list (`?page=&page_size=`) |
| GET  | `/jobs/{job_id}` | Job detail with audio metadata |
| GET  | `/jobs/{job_id}/status` | Poll `{ status, stage, progress }` |
| POST | `/jobs/{job_id}/cancel` | Cancel a pending/running job |

**Example — upload**
```bash
curl -X POST http://localhost:8000/api/v1/audio/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@conversation.wav;type=audio/wav'
```

Allowed types: `wav, mp3, aac, ogg, m4a, flac` · max 100 MB.

## Results & reports

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/results/{job_id}` | Full analysis (409 until job `completed`) |
| POST | `/reports/{job_id}/generate` | Build the PDF report |
| GET  | `/reports/{job_id}/download` | Download the PDF (`application/pdf`) |

**`/results/{job_id}` (200) shape**
```json
{
  "job_id": "…", "status": "completed", "detected_speakers": 2,
  "language_source": "kn", "language_target": "en",
  "processing_time_seconds": 12.4,
  "audio": { "original_filename": "conv.wav", "duration_seconds": 95.2,
             "sample_rate": 16000, "channels": 1 },
  "speakers": [
    {
      "label": "A", "color": "#6366F1",
      "total_speech_seconds": 48.1, "total_pause_seconds": 6.3,
      "segment_count": 12, "word_count": 140,
      "prediction": {
        "gender": "unknown", "age_group": "unknown",
        "atypicality": "typical", "atypicality_score": 0.12,
        "atypicality_confidence": 0.67
      },
      "transcriptions": [
        { "start_time": 0.0, "end_time": 3.0,
          "text_source": "ನಮಸ್ಕಾರ", "text_translated": "Hello",
          "confidence": 0.9 }
      ]
    }
  ],
  "has_report": false
}
```

## Admin (role: admin)

| Method | Path | Description |
|--------|------|-------------|
| GET   | `/admin/users` | Paginated user list |
| PATCH | `/admin/users/{id}/role` | Change a user's role |
| PATCH | `/admin/users/{id}/deactivate` | Disable an account |
| GET   | `/admin/audit-logs` | Paginated audit trail |

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness (checks the database) |

## Status codes

`200` ok · `201` created · `202` accepted (async) · `400` invalid file ·
`401` unauthenticated · `403` forbidden · `404` not found · `409` conflict
(e.g. results not ready) · `422` validation · `429` rate limited · `5xx` server.
