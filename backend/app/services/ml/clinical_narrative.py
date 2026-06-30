"""Clinical narrative generation using Google Gemini.

After analysis completes, this service generates a 3-4 sentence clinical
summary for each speaker, translating acoustic features and predictions into
actionable clinical language suitable for mental health professionals while
remaining technically informative for evaluation purposes.
"""

from __future__ import annotations

import json
import re
import threading
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.services.ml.types import (
    AcousticFeatures,
    AtypicalityPrediction,
    GenderAgePrediction,
)

logger = get_logger(__name__)

_NARRATIVE_PROMPT = """You are an expert clinical phonetician and speech-language pathologist writing concise clinical assessments for mental health professionals.

Given the following acoustic analysis data for a single speaker, write a 3-4 sentence clinical narrative that:
1. Highlights clinically significant acoustic deviations (jitter, shimmer, HNR, F0, pauses)
2. Relates findings to potential speech motor or prosodic difficulties
3. Mentions the atypicality assessment and confidence level
4. Includes predicted demographic information (gender/age) with the analysis method noted
5. Uses precise technical terminology while remaining actionable

Be direct and clinical. Focus on what the data reveals about speech characteristics that may warrant follow-up.

Acoustic Features:
- Latency to Speak: {latency:.3f} seconds
- Pause-to-Speech Ratio: {pause_ratio:.3f}
- F0 Mean: {f0_mean:.1f} Hz (std: {f0_std:.1f} Hz)
- Jitter: {jitter:.4f}
- Shimmer: {shimmer:.4f}
- HNR: {hnr:.2f} dB
- Speech Rate: {speech_rate:.1f} words/sec
- Pronunciation Flux Variance: {flux_var:.4f}

Predictions:
- Gender: {gender} ({gender_conf:.1%} confidence, via {gender_source})
- Age Group: {age_group} ({age_conf:.1%} confidence)
- Atypicality: {atyp_label} (score: {atyp_score:.3f}, confidence: {atyp_conf:.1%})

Response format: Plain text paragraph only, 3-4 sentences, no JSON or markdown."""


def _safe_value(value: float | None, default: float = 0.0) -> float:
    """Return value or default if None."""
    return value if value is not None else default


class ClinicalNarrativeGenerator:
    """Lazily-initialized Gemini client for generating clinical narratives."""

    def __init__(self) -> None:
        self._client: Any = None
        self._checked = False
        self._lock = threading.Lock()

    @property
    def is_available(self) -> bool:
        """Check if Gemini API is configured and ready."""
        if not settings.GEMINI_API_KEY:
            return False
        self._ensure_client()
        return self._client is not None

    def _ensure_client(self) -> None:
        """Initialize Gemini client (thread-safe, once per process)."""
        if self._checked:
            return
        with self._lock:
            if self._checked:
                return
            self._checked = True
            if not settings.GEMINI_API_KEY:
                return
            try:
                from google import genai

                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("gemini_narrative_client_ready", model=settings.GEMINI_MODEL)
            except Exception as exc:  # noqa: BLE001
                logger.warning("gemini_narrative_client_unavailable", error=str(exc))
                self._client = None

    def generate(
        self,
        features: AcousticFeatures | None,
        gender_age: GenderAgePrediction | None,
        atypicality: AtypicalityPrediction | None,
    ) -> str | None:
        """Generate clinical narrative for a single speaker.
        
        Returns None if generation fails or is unavailable. The caller should
        handle gracefully (e.g., display results without narrative).
        """
        if not self.is_available or features is None:
            return None

        try:
            # Build the prompt with actual values
            prompt = _NARRATIVE_PROMPT.format(
                latency=_safe_value(features.latency_to_speak_sec),
                pause_ratio=_safe_value(features.pause_to_speech_ratio),
                f0_mean=_safe_value(features.f0_mean),
                f0_std=_safe_value(features.f0_std),
                jitter=_safe_value(features.jitter),
                shimmer=_safe_value(features.shimmer),
                hnr=_safe_value(features.hnr),
                speech_rate=_safe_value(features.speech_rate),
                flux_var=_safe_value(features.pronunciation_flux_var),
                gender=gender_age.gender if gender_age else "unknown",
                gender_conf=_safe_value(gender_age.gender_confidence if gender_age else None, 0.0),
                gender_source=gender_age.source if gender_age else "model",
                age_group=gender_age.age_group if gender_age else "unknown",
                age_conf=_safe_value(gender_age.age_confidence if gender_age else None, 0.0),
                atyp_label=atypicality.label if atypicality else "unknown",
                atyp_score=_safe_value(atypicality.score if atypicality else None),
                atyp_conf=_safe_value(atypicality.confidence if atypicality else None, 0.0),
            )

            from google.genai import types

            response = self._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Slightly creative but consistent
                    max_output_tokens=300,  # ~3-4 sentences
                ),
            )

            narrative = getattr(response, "text", "") or ""
            narrative = narrative.strip()

            if not narrative:
                logger.warning("gemini_narrative_empty_response")
                return None

            logger.info("gemini_narrative_generated", length=len(narrative))
            return narrative

        except Exception as exc:  # noqa: BLE001
            logger.warning("gemini_narrative_failed", error=str(exc))
            return None


# --------------------------------------------------------------- singleton
_instance: ClinicalNarrativeGenerator | None = None
_instance_lock = threading.Lock()


def get_clinical_narrative_generator() -> ClinicalNarrativeGenerator:
    """Return the process-wide singleton narrative generator."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = ClinicalNarrativeGenerator()
    return _instance
