"""Report endpoints: generate and download the PDF analysis report."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import Report, User
from app.models.enums import AuditAction, JobStatus
from app.schemas.report import ReportRead
from app.services import auth_service, job_service
from app.services.report_generator import build_context_from_job, get_report_generator
from app.services.storage import get_storage

logger = get_logger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_filename(job_id: uuid.UUID) -> str:
    return f"ablepro_report_{str(job_id)[:8]}.pdf"


@router.post(
    "/{job_id}/generate",
    response_model=ReportRead,
    summary="Generate (or regenerate) the PDF report for a completed job",
)
async def generate_report(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportRead:
    job = job_service.get_job_with_results(db, job_id, user=user)
    if job.status != JobStatus.COMPLETED:
        raise ConflictError(
            "A report can only be generated for a completed job.",
            code="job_not_completed",
        )

    # Add a transparency note only if any speaker is STILL unknown after the
    # optional LLM fallback (i.e. neither the model nor Gemini could classify).
    model_note = None
    still_unknown = any(
        sp.prediction is None
        or sp.prediction.gender.value == "unknown"
        or sp.prediction.age_group.value == "unknown"
        for sp in job.speakers
    )
    if still_unknown:
        model_note = (
            "Some gender/age predictions could not be determined. The bundled "
            "gender/age model is single-class; enable the Gemini audio fallback "
            "(GEMINI_API_KEY) for automatic estimation."
        )

    ctx = build_context_from_job(job, user, model_note=model_note)
    pdf_bytes, page_count = get_report_generator().generate(ctx)

    filename = _report_filename(job.id)
    storage_path = f"reports/{job.user_id}/{job.id}.pdf"
    get_storage().upload(storage_path, pdf_bytes, "application/pdf")

    report = job.report
    if report is None:
        report = Report(
            job_id=job.id,
            storage_bucket=settings.SUPABASE_STORAGE_BUCKET,
            storage_path=storage_path,
            filename=filename,
        )
        db.add(report)
    report.storage_path = storage_path
    report.filename = filename
    report.size_bytes = len(pdf_bytes)
    report.page_count = page_count
    db.flush()
    db.commit()

    return ReportRead.model_validate(report)


@router.get(
    "/{job_id}/download",
    summary="Download the generated PDF report",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def download_report(
    job_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    job = job_service.get_job_with_results(db, job_id, user=user)
    report = job.report

    if report is None:
        # Lazily generate on first download for convenience.
        await generate_report(job_id, db=db, user=user)
        db.expire_all()
        job = job_service.get_job_with_results(db, job_id, user=user)
        report = job.report

    if report is None:
        raise NotFoundError("Report could not be generated. Please try again.")

    pdf_bytes = get_storage().download(report.storage_path)

    auth_service.record_audit(
        db,
        action=AuditAction.DOWNLOAD_REPORT,
        user_id=user.id,
        resource_type="report",
        resource_id=str(report.id),
        ip_address=client_ip(request),
    )

    def _iter():
        yield pdf_bytes

    return StreamingResponse(
        _iter(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report.filename}"'},
    )