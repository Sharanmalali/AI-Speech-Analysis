"""Job lifecycle and result-persistence business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.models import AudioFile, Job, Prediction, Speaker, Transcription, User
from app.models.enums import (
    AgeGroup,
    AtypicalityLabel,
    Gender,
    JobStage,
    JobStatus,
    UserRole,
)
from app.services.ml.types import PipelineResult

logger = get_logger(__name__)


def create_job(db: Session, *, user: User, audio_file: AudioFile) -> Job:
    job = Job(
        user_id=user.id,
        audio_file_id=audio_file.id,
        status=JobStatus.PENDING,
        stage=JobStage.UPLOADED,
        progress=0.0,
    )
    db.add(job)
    db.flush()
    logger.info("job_created", job_id=str(job.id), user_id=str(user.id))
    return job


def get_job(db: Session, job_id: uuid.UUID | str, *, user: User) -> Job:
    job = db.get(Job, job_id if isinstance(job_id, uuid.UUID) else _to_uuid(job_id))
    if job is None:
        raise NotFoundError("Job not found.")
    _authorize(job, user)
    return job


def get_job_with_results(db: Session, job_id: uuid.UUID | str, *, user: User) -> Job:
    stmt = (
        select(Job)
        .where(Job.id == (job_id if isinstance(job_id, uuid.UUID) else _to_uuid(job_id)))
        .options(
            selectinload(Job.audio_file),
            selectinload(Job.report),
            selectinload(Job.speakers).selectinload(Speaker.prediction),
            selectinload(Job.speakers).selectinload(Speaker.transcriptions),
        )
    )
    job = db.execute(stmt).scalar_one_or_none()
    if job is None:
        raise NotFoundError("Job not found.")
    _authorize(job, user)
    return job


def list_jobs(db: Session, *, user: User, offset: int = 0, limit: int = 20) -> tuple[list[Job], int]:
    base = select(Job).options(selectinload(Job.audio_file))
    count_stmt = select(func.count()).select_from(Job)
    # Non-privileged users only see their own jobs.
    if user.role not in (UserRole.ADMIN, UserRole.DOCTOR):
        base = base.where(Job.user_id == user.id)
        count_stmt = count_stmt.where(Job.user_id == user.id)

    total = db.execute(count_stmt).scalar_one()
    rows = (
        db.execute(base.order_by(Job.created_at.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), int(total)


def update_progress(db: Session, job: Job, stage: JobStage, progress: float) -> None:
    job.stage = stage
    job.progress = float(progress)
    if job.status == JobStatus.PENDING:
        job.status = JobStatus.PROCESSING
    db.add(job)
    db.flush()


def mark_processing(db: Session, job: Job, *, task_id: str | None = None) -> None:
    job.status = JobStatus.PROCESSING
    job.started_at = datetime.now(UTC)
    if task_id:
        job.task_id = task_id
    db.add(job)
    db.flush()


def mark_failed(db: Session, job: Job, *, error: str) -> None:
    job.status = JobStatus.FAILED
    job.error_message = error[:2000]
    job.finished_at = datetime.now(UTC)
    db.add(job)
    db.flush()
    logger.error("job_failed", job_id=str(job.id), error=error)


def delete_job(db: Session, job_id: uuid.UUID | str, *, user: User) -> None:
    """Delete a job, its results, the source audio file and stored objects.

    ORM cascades remove the job's speakers/transcriptions/predictions/report
    rows; the parent ``AudioFile`` row is removed explicitly. Storage objects
    (audio + generated report) are best-effort cleaned up — a storage failure
    never blocks the database deletion.
    """
    job = get_job_with_results(db, job_id, user=user)

    # Best-effort: cancel a still-running Celery task before deleting.
    if job.status in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING) and job.task_id:
        try:
            from app.tasks.celery_app import celery_app

            celery_app.control.revoke(job.task_id, terminate=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("revoke_on_delete_failed", job_id=str(job.id), error=str(exc))

    # Collect storage object paths before the rows are gone.
    storage_paths: list[str] = []
    audio_file = job.audio_file
    if audio_file is not None and audio_file.storage_path:
        storage_paths.append(audio_file.storage_path)
    if job.report is not None and job.report.storage_path:
        storage_paths.append(job.report.storage_path)

    # Remove objects from storage (non-fatal).
    if storage_paths:
        try:
            from app.services.storage import get_storage

            storage = get_storage()
            for path in storage_paths:
                try:
                    storage.delete(path)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("storage_delete_failed", path=path, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.warning("storage_backend_unavailable", error=str(exc))

    # Delete the job (ORM cascade removes speakers/transcriptions/predictions/report),
    # then the orphaned audio file row.
    db.delete(job)
    if audio_file is not None:
        db.delete(audio_file)
    db.flush()
    logger.info("job_deleted", job_id=str(job.id), user_id=str(user.id))


def persist_result(db: Session, job: Job, result: PipelineResult) -> None:
    """Persist a completed :class:`PipelineResult` into the relational model."""
    job.detected_speakers = result.detected_speakers
    job.processing_time_seconds = result.processing_time_seconds

    # Backfill authoritative audio metadata computed during processing.
    # The upload-time probe is best-effort and is skipped entirely when the
    # storage backend exposes no local path (e.g. Supabase), and libsndfile
    # cannot read mp3/m4a/aac — so the audio_file row frequently has no
    # duration and the results card shows 00:00. The pipeline decodes the full
    # signal, so its duration is reliable; write it back here.
    audio_file = job.audio_file
    if audio_file is not None:
        duration = result.duration_seconds
        if not duration or duration <= 0:
            # Fallback: furthest transcript end across all speakers.
            ends = [seg.end for sp in result.speakers for seg in sp.segments]
            duration = max(ends) if ends else None
        if duration and duration > 0:
            audio_file.duration_seconds = round(float(duration), 3)
        if result.sample_rate and not audio_file.sample_rate:
            audio_file.sample_rate = int(result.sample_rate)
        db.add(audio_file)

    for sr in result.speakers:
        speaker = Speaker(
            job_id=job.id,
            label=sr.label,
            diarization_id=sr.diarization_id,
            color=sr.color,
            total_speech_seconds=sr.total_speech_seconds,
            total_pause_seconds=sr.total_pause_seconds,
            segment_count=sr.segment_count,
            word_count=sr.word_count,
        )
        db.add(speaker)
        db.flush()

        for seg in sr.segments:
            db.add(
                Transcription(
                    speaker_id=speaker.id,
                    start_time=seg.start,
                    end_time=seg.end,
                    text_source=seg.text_source,
                    text_translated=seg.text_translated,
                    confidence=seg.confidence,
                )
            )

        ga = sr.gender_age
        at = sr.atypicality
        feature_payload = None
        if sr.features is not None:
            feature_payload = sr.features.as_dict()
            if ga is not None:
                # Stash the prediction provenance alongside the features so we
                # avoid a schema migration; surfaced via Prediction.gender_age_source.
                feature_payload["gender_age_source"] = ga.source
            # Store feature contributions for explainability
            if at and at.feature_contributions:
                feature_payload["feature_contributions"] = at.feature_contributions
        db.add(
            Prediction(
                speaker_id=speaker.id,
                gender=Gender(ga.gender) if ga else Gender.UNKNOWN,
                gender_confidence=ga.gender_confidence if ga else None,
                age_group=AgeGroup(ga.age_group) if ga else AgeGroup.UNKNOWN,
                age_confidence=ga.age_confidence if ga else None,
                raw_class_label=ga.raw_label if ga else None,
                atypicality=AtypicalityLabel(at.label) if at else AtypicalityLabel.UNKNOWN,
                atypicality_score=at.score if at else None,
                atypicality_confidence=at.confidence if at else None,
                features=feature_payload,
            )
        )

    job.status = JobStatus.COMPLETED
    job.stage = JobStage.DONE
    job.progress = 100.0
    job.finished_at = datetime.now(UTC)
    db.add(job)
    db.flush()
    logger.info("job_results_persisted", job_id=str(job.id), speakers=len(result.speakers))


# --------------------------------------------------------------- helpers
def _authorize(job: Job, user: User) -> None:
    if user.role in (UserRole.ADMIN, UserRole.DOCTOR):
        return
    if job.user_id != user.id:
        raise AuthorizationError("You do not have access to this job.")


def _to_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise NotFoundError("Job not found.") from exc
