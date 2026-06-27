"""Celery application factory.

Long-running audio analysis is executed by Celery workers so the API stays
responsive. Redis is used as both broker and result backend.
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "ablepro",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["app.tasks.pipeline_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,                  # re-deliver if a worker crashes mid-task
    worker_prefetch_multiplier=1,         # fair dispatch for long tasks
    task_time_limit=60 * 30,              # hard limit: 30 min
    task_soft_time_limit=60 * 25,         # soft limit: 25 min
    result_expires=60 * 60 * 24,          # keep results 24h
    broker_connection_retry_on_startup=True,
)
