"""Task dispatch helpers that decouple routers from Celery internals."""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


def enqueue_audio_job(job_id: str) -> str | None:
    """Queue the audio-processing task. Returns the Celery task id (or None).

    Import is deferred so the API process does not import the heavy task
    module (and its transitive ML imports) unless dispatching.
    """
    try:
        from app.tasks.pipeline_tasks import process_audio_job

        async_result = process_audio_job.delay(job_id)
        logger.info("job_enqueued", job_id=job_id, task_id=async_result.id)
        return async_result.id
    except Exception as exc:  # noqa: BLE001
        # Broker unavailable — surface as a soft failure; the job stays PENDING
        # and can be retried. Never crash the request because of the broker.
        logger.error("job_enqueue_failed", job_id=job_id, error=str(exc))
        return None
