"""Job management endpoints: list, detail, status polling and cancellation."""

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import User
from app.models.enums import AuditAction, JobStatus
from app.schemas.common import Page
from app.schemas.job import JobStatusResponse, JobWithAudio
from app.services import auth_service, job_service

logger = get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=Page[JobWithAudio], summary="List jobs (paginated)")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[JobWithAudio]:
    offset = (page - 1) * page_size
    rows, total = job_service.list_jobs(db, user=user, offset=offset, limit=page_size)
    return Page[JobWithAudio](
        items=[JobWithAudio.model_validate(j) for j in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobWithAudio, summary="Get a job")
async def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JobWithAudio:
    job = job_service.get_job_with_results(db, job_id, user=user)
    return JobWithAudio.model_validate(job)


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Poll job status & progress",
)
async def job_status(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JobStatusResponse:
    job = job_service.get_job(db, job_id, user=user)
    return JobStatusResponse(
        id=job.id,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        detected_speakers=job.detected_speakers,
        error_message=job.error_message,
    )


@router.post(
    "/{job_id}/cancel",
    response_model=JobStatusResponse,
    summary="Cancel a pending or running job",
)
async def cancel_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JobStatusResponse:
    job = job_service.get_job(db, job_id, user=user)
    if job.status in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING):
        # Best-effort revoke of the Celery task.
        if job.task_id:
            try:
                from app.tasks.celery_app import celery_app

                celery_app.control.revoke(job.task_id, terminate=True)
            except Exception as exc:  # noqa: BLE001
                logger.warning("revoke_failed", job_id=str(job.id), error=str(exc))
        job.status = JobStatus.CANCELLED
        db.add(job)
        db.flush()
    return JobStatusResponse(
        id=job.id, status=job.status, stage=job.stage, progress=job.progress
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job, its results and the source audio",
)
async def delete_job(
    job_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    job_service.delete_job(db, job_id, user=user)
    auth_service.record_audit(
        db,
        action=AuditAction.DELETE_AUDIO,
        user_id=user.id,
        resource_type="job",
        resource_id=str(job_id),
        ip_address=client_ip(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
