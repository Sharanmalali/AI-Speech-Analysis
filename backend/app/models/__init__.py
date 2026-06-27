"""SQLAlchemy ORM models.

Importing this package registers every model on the shared declarative
``Base.metadata`` so Alembic autogenerate and ``create_all`` see them.
"""

from app.models.audio_file import AudioFile
from app.models.audit_log import AuditLog
from app.models.enums import (
    AgeGroup,
    AtypicalityLabel,
    AuditAction,
    Gender,
    JobStage,
    JobStatus,
    UserRole,
)
from app.models.job import Job
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.speaker import Speaker
from app.models.transcription import Transcription
from app.models.user import User

__all__ = [
    "User",
    "AudioFile",
    "Job",
    "Speaker",
    "Transcription",
    "Prediction",
    "Report",
    "AuditLog",
    # enums
    "UserRole",
    "JobStatus",
    "JobStage",
    "Gender",
    "AgeGroup",
    "AtypicalityLabel",
    "AuditAction",
]
