"""Enumerations shared across ORM models and schemas."""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """Role-based access control roles."""

    ADMIN = "admin"
    DOCTOR = "doctor"
    USER = "user"


class JobStatus(str, enum.Enum):
    """Lifecycle states of an audio processing job."""

    PENDING = "pending"          # created, queued
    QUEUED = "queued"            # accepted by the broker
    PROCESSING = "processing"    # pipeline running
    COMPLETED = "completed"      # results stored
    FAILED = "failed"            # terminal error
    CANCELLED = "cancelled"      # cancelled by user/admin


class JobStage(str, enum.Enum):
    """Granular pipeline stages used for progress reporting."""

    UPLOADED = "uploaded"
    NOISE_REDUCTION = "noise_reduction"
    DIARIZATION = "diarization"
    SEGMENTATION = "segmentation"
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    FEATURE_EXTRACTION = "feature_extraction"
    GENDER_PREDICTION = "gender_prediction"
    AGE_PREDICTION = "age_prediction"
    ATYPICALITY_CLASSIFICATION = "atypicality_classification"
    AGGREGATION = "aggregation"
    REPORT_GENERATION = "report_generation"
    DONE = "done"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class AgeGroup(str, enum.Enum):
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"
    SENIOR = "senior"
    UNKNOWN = "unknown"


class AtypicalityLabel(str, enum.Enum):
    TYPICAL = "typical"
    ATYPICAL = "atypical"
    UNKNOWN = "unknown"


class AuditAction(str, enum.Enum):
    """Auditable actions for the compliance trail."""

    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    UPLOAD_AUDIO = "upload_audio"
    CREATE_JOB = "create_job"
    VIEW_RESULT = "view_result"
    DOWNLOAD_REPORT = "download_report"
    DELETE_AUDIO = "delete_audio"
    ROLE_CHANGED = "role_changed"
