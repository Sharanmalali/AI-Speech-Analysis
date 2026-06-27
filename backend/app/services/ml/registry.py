"""Central registry for the ML services.

Provides singleton accessors and a ``warmup_models`` entrypoint (called from
the FastAPI lifespan) that eagerly initialises each independent service once,
so the first user request does not pay the cold-start cost.

Each service remains fully independent — the registry only coordinates their
lifecycle; it never merges them into a single object.
"""

from __future__ import annotations

from app.config import settings
from app.core.logging import get_logger
from app.services.ml.atypicality_classifier import get_atypicality_classifier
from app.services.ml.gender_age_classifier import get_gender_age_classifier

logger = get_logger(__name__)


def warmup_models(*, include_heavy: bool = True) -> dict[str, str]:
    """Eagerly load available models. Returns a per-service status map.

    The lightweight scikit-learn models (atypicality, gender/age) are always
    warmed. The heavy services (diarization, transcription) are warmed only
    when ``include_heavy`` is true and their prerequisites (HF token, model
    downloads) are satisfied; failures are logged but never fatal so the API
    can still serve non-inference traffic.
    """
    status: dict[str, str] = {}

    # --- Lightweight sklearn services (always) ------------------------------
    try:
        get_atypicality_classifier().load()
        status["atypicality"] = "ready"
    except Exception as exc:  # noqa: BLE001
        status["atypicality"] = f"error: {exc}"
        logger.warning("warmup_atypicality_failed", error=str(exc))

    try:
        clf = get_gender_age_classifier()
        clf.load()
        status["gender_age"] = "degenerate" if clf.is_degenerate else "ready"
    except Exception as exc:  # noqa: BLE001
        status["gender_age"] = f"error: {exc}"
        logger.warning("warmup_gender_age_failed", error=str(exc))

    # --- Heavy services (best-effort) ---------------------------------------
    if include_heavy:
        try:
            from app.services.ml.hf_gender_age import get_hf_gender_age_classifier

            hf = get_hf_gender_age_classifier()
            if hf.is_enabled:
                hf.load()
                status["hf_gender_age"] = "ready" if hf.is_loaded else "unavailable"
            else:
                status["hf_gender_age"] = "disabled"
        except Exception as exc:  # noqa: BLE001
            status["hf_gender_age"] = f"error: {exc}"
            logger.warning("warmup_hf_gender_age_failed", error=str(exc))

        try:
            from app.services.ml.speaker_diarization import get_diarization_service

            if settings.HUGGINGFACE_TOKEN:
                get_diarization_service().load()
                status["diarization"] = "ready"
            else:
                status["diarization"] = "skipped: no HF token"
        except Exception as exc:  # noqa: BLE001
            status["diarization"] = f"error: {exc}"
            logger.warning("warmup_diarization_failed", error=str(exc))

        try:
            from app.services.ml.transcription import get_transcription_service

            get_transcription_service().load()
            status["transcription"] = "ready"
        except Exception as exc:  # noqa: BLE001
            status["transcription"] = f"error: {exc}"
            logger.warning("warmup_transcription_failed", error=str(exc))

    logger.info("model_warmup_status", **status)
    return status


def model_status() -> dict[str, bool]:
    """Lightweight readiness snapshot for health/diagnostics endpoints."""
    from app.services.ml.hf_gender_age import get_hf_gender_age_classifier

    return {
        "atypicality": get_atypicality_classifier().is_loaded,
        "gender_age": get_gender_age_classifier().is_loaded,
        "hf_gender_age": get_hf_gender_age_classifier().is_loaded,
    }
