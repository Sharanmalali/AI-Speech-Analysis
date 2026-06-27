"""Application configuration.

All configuration is sourced from environment variables (12-factor app).
Values are validated and typed via Pydantic Settings v2. Never hard-code
secrets — provide them through the environment or a local ``.env`` file
(which must never be committed).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Repository root:  <repo>/backend/app/config/settings.py -> parents[3] == <repo>
REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=(BACKEND_ROOT / ".env", REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ App
    APP_NAME: str = "AblePro Solutions"
    APP_DESCRIPTION: str = (
        "AI-powered Multi-speaker Mental Health Audio Analytics Platform"
    )
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --------------------------------------------------------------- Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # ----------------------------------------------------------------- CORS
    # Comma-separated list of allowed origins, e.g.
    # "http://localhost:3000,https://app.ablepro.ai"
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    CORS_ALLOW_CREDENTIALS: bool = True

    # ------------------------------------------------------------- Security
    # JWT signing secret — MUST be overridden in every non-dev environment.
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Cookie settings for refresh tokens.
    SECURE_COOKIES: bool = False  # True behind HTTPS in production
    COOKIE_DOMAIN: str | None = None
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    # ------------------------------------------------------------- Database
    DATABASE_URL: PostgresDsn | None = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # ------------------------------------------------------------- Supabase
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_JWT_SECRET: str | None = None
    SUPABASE_STORAGE_BUCKET: str = "audio-uploads"

    # ---------------------------------------------------------------- Redis
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # --------------------------------------------------------- Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_UPLOAD: str = "5/minute"
    RATE_LIMIT_ANONYMOUS: str = "20/minute"

    # ------------------------------------------------------------- Uploads
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_AUDIO_EXTENSIONS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["wav", "mp3", "aac", "ogg", "m4a", "flac"]
    )
    ALLOWED_AUDIO_MIME_TYPES: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "audio/wav",
            "audio/x-wav",
            "audio/wave",
            "audio/mpeg",
            "audio/mp3",
            "audio/aac",
            "audio/ogg",
            "audio/x-m4a",
            "audio/mp4",
            "audio/flac",
            "audio/x-flac",
        ]
    )
    UPLOAD_TMP_DIR: Path = BACKEND_ROOT / "storage" / "tmp"
    REPORT_OUTPUT_DIR: Path = BACKEND_ROOT / "storage" / "reports"

    # ------------------------------------------------------ ML model paths
    MODELS_DIR: Path = REPO_ROOT / "models"
    ATYPICALITY_SCALER_PATH: Path | None = None
    ATYPICALITY_IFOREST_PATH: Path | None = None
    GENDER_AGE_MODEL_PATH: Path | None = None

    # Whisper / transcription
    WHISPER_MODEL_SIZE: str = "small"  # tiny|base|small|medium|large-v3
    WHISPER_DEVICE: Literal["cpu", "cuda", "auto"] = "auto"
    WHISPER_COMPUTE_TYPE: str = "int8"  # for faster-whisper on cpu
    TRANSCRIPTION_SOURCE_LANGUAGE: str = "kn"  # Kannada
    TRANSCRIPTION_TARGET_LANGUAGE: str = "en"  # English

    # Pyannote diarization
    PYANNOTE_PIPELINE: str = "pyannote/speaker-diarization-3.1"
    HUGGINGFACE_TOKEN: str | None = None
    DIARIZATION_DEVICE: Literal["cpu", "cuda", "auto"] = "auto"
    MIN_SPEAKERS: int | None = None
    MAX_SPEAKERS: int | None = None

    # Audio processing
    TARGET_SAMPLE_RATE: int = 16000
    ENABLE_NOISE_REDUCTION: bool = True

    # ------------------------------------------- LLM gender/age fallback
    # When the local gender/age model returns "unknown", optionally ask a
    # multimodal LLM (Google Gemini) to classify the speaker's voice. Fully
    # optional: with no API key the fallback is silently skipped.
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GENDER_AGE_LLM_FALLBACK: bool = True
    # Max seconds of a speaker's audio to send to the LLM (keeps payload small
    # and well under inline-data limits; plenty for gender/age estimation).
    LLM_AUDIO_MAX_SECONDS: int = 30

    # ------------------------------------- HF wav2vec2 gender / age models
    # Dedicated Hugging Face audio-classification models for per-speaker gender
    # and age-group prediction. When enabled and loadable, they are the PRIMARY
    # source for gender/age. The legacy sklearn model and the Gemini fallback
    # remain in place as graceful fallbacks, so the pipeline never breaks if
    # these models are disabled or fail to download/load.
    GENDER_AGE_HF_ENABLED: bool = True
    GENDER_MODEL_ID: str = "alefiury/wav2vec2-large-xlsr-53-gender-recognition-librispeech"
    AGE_MODEL_ID: str = "anantoj/wav2vec2-xls-r-300m-adult-child-cls"
    GENDER_AGE_HF_DEVICE: Literal["cpu", "cuda", "auto"] = "auto"
    # Cap on seconds of speaker audio fed to the wav2vec2 models (bounds memory
    # and latency for very talkative speakers; ample for gender/age inference).
    GENDER_AGE_HF_MAX_SECONDS: int = 30

    # --------------------------------------------------------------- Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_JSON: bool = False  # True for structured JSON logs in production

    # ------------------------------------------------------------ Validators
    @field_validator("CORS_ORIGINS", "ALLOWED_AUDIO_EXTENSIONS", "ALLOWED_AUDIO_MIME_TYPES", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow comma-separated strings for list-typed env vars."""
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return value  # let pydantic parse JSON-style lists
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @field_validator(
        "DATABASE_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "HUGGINGFACE_TOKEN",
        "GEMINI_API_KEY",
        "COOKIE_DOMAIN",
        mode="before",
    )
    @classmethod
    def _empty_str_to_none(cls, value: object) -> object:
        """Treat empty/blank env strings as unset (None)."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    # --------------------------------------------------------- Derived props
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or str(self.REDIS_URL)

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or str(self.REDIS_URL)

    @property
    def scaler_path(self) -> Path:
        return self.ATYPICALITY_SCALER_PATH or (self.MODELS_DIR / "atypicality_scaler.pkl")

    @property
    def iforest_path(self) -> Path:
        return self.ATYPICALITY_IFOREST_PATH or (self.MODELS_DIR / "atypicality_iforest.pkl")

    @property
    def gender_age_path(self) -> Path:
        return self.GENDER_AGE_MODEL_PATH or (self.MODELS_DIR / "gender_age_clf.pkl")

    @property
    def database_url_sync(self) -> str:
        """SQLAlchemy URL using the psycopg (v3) driver."""
        if self.DATABASE_URL is None:
            # Local fallback so the app can boot without Supabase configured.
            return "sqlite:///./ablepro_dev.db"
        url = str(self.DATABASE_URL)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton ``Settings`` instance."""
    return Settings()


settings = get_settings()
