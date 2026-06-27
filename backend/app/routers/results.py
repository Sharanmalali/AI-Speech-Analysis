"""Results endpoint: the complete analysis payload for the dashboard."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import User
from app.models.enums import AuditAction, JobStatus
from app.schemas.results import (
    AudioSummary,
    PredictionRead,
    ResultResponse,
    SpeakerRead,
    TranscriptionRead,
)
from app.services import auth_service, job_service

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{job_id}", response_model=ResultResponse, summary="Get full analysis results")
async def get_results(
    job_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultResponse:
    job = job_service.get_job_with_results(db, job_id, user=user)
    if job.status != JobStatus.COMPLETED:
        raise ConflictError(
            f"Results are not ready (job status: {job.status.value}).",
            code="results_not_ready",
            details={"status": job.status.value, "progress": job.progress},
        )

    speakers = [
        SpeakerRead(
            id=sp.id,
            label=sp.label,
            diarization_id=sp.diarization_id,
            color=sp.color,
            total_speech_seconds=sp.total_speech_seconds,
            total_pause_seconds=sp.total_pause_seconds,
            segment_count=sp.segment_count,
            word_count=sp.word_count,
            prediction=PredictionRead.model_validate(sp.prediction) if sp.prediction else None,
            transcriptions=[
                TranscriptionRead.model_validate(t)
                for t in sorted(sp.transcriptions, key=lambda t: t.start_time)
            ],
        )
        for sp in sorted(job.speakers, key=lambda s: s.label)
    ]

    auth_service.record_audit(
        db,
        action=AuditAction.VIEW_RESULT,
        user_id=user.id,
        resource_type="job",
        resource_id=str(job.id),
        ip_address=client_ip(request),
    )

    # Duration: prefer the stored value; for older jobs whose upload-time probe
    # was skipped (no stored duration), fall back to the furthest transcript
    # end so the results card never shows 00:00 for a real recording.
    duration_seconds = job.audio_file.duration_seconds
    if not duration_seconds or duration_seconds <= 0:
        ends = [
            t.end_time
            for sp in job.speakers
            for t in sp.transcriptions
            if t.end_time is not None
        ]
        duration_seconds = round(max(ends), 3) if ends else duration_seconds

    return ResultResponse(
        job_id=job.id,
        status=job.status,
        detected_speakers=job.detected_speakers or len(speakers),
        language_source="kn",
        language_target="en",
        processing_time_seconds=job.processing_time_seconds,
        audio=AudioSummary(
            duration_seconds=duration_seconds,
            sample_rate=job.audio_file.sample_rate,
            channels=job.audio_file.channels,
            original_filename=job.audio_file.original_filename,
        ),
        speakers=speakers,
        has_report=job.report is not None,
    )
