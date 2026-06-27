"""LLM-based gender & age fallback (Google Gemini, multimodal audio).

When the local ``gender_age_clf`` model returns ``unknown`` (it was trained on
a single class and is therefore uninformative), we optionally send the
speaker's short audio clip to Gemini, which natively understands audio, and
ask it to classify the voice as man / woman / child plus an age group.

The service is fully optional and degrades gracefully:
* no ``GEMINI_API_KEY``            -> :meth:`is_available` is False, no calls.
* ``google-genai`` not installed   -> disabled with a logged warning.
* any API/parse error              -> returns ``None`` (caller keeps "unknown").
"""

from __future__ import annotations

import json
import re
import threading
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.models.enums import AgeGroup, Gender
from app.services.ml.types import GenderAgePrediction

logger = get_logger(__name__)

_PROMPT = (
    "You are an expert phonetician analysing a short audio clip containing the "
    "voice of a SINGLE speaker. Based only on vocal characteristics (pitch, "
    "timbre, resonance, articulation), classify the speaker. Do not transcribe. "
    "Respond with STRICT JSON only, no prose, using exactly this shape:\n"
    '{"gender": "male|female|unknown", '
    '"age_group": "child|teen|adult|senior|unknown", '
    '"category": "man|woman|child", '
    '"confidence": 0.0}\n'
    "Use 'child' for clearly pre-pubescent voices regardless of gender. "
    "confidence is your certainty from 0 to 1."
)

_GENDER_TOKENS = {g.value: g for g in Gender}
_AGE_TOKENS = {a.value: a for a in AgeGroup}


def _extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first JSON object out of the model's response text."""
    if not text:
        return None
    text = text.strip()
    # Strip ```json fences if present.
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _interpret(payload: dict[str, Any]) -> GenderAgePrediction:
    """Map the LLM JSON payload onto the domain prediction type."""
    gender = _GENDER_TOKENS.get(str(payload.get("gender", "")).lower(), Gender.UNKNOWN)
    age = _AGE_TOKENS.get(str(payload.get("age_group", "")).lower(), AgeGroup.UNKNOWN)
    category = str(payload.get("category", "")).lower()

    # The simple man/woman/child category refines the detailed fields.
    if category == "man":
        gender = Gender.MALE if gender == Gender.UNKNOWN else gender
        age = AgeGroup.ADULT if age == AgeGroup.UNKNOWN else age
    elif category == "woman":
        gender = Gender.FEMALE if gender == Gender.UNKNOWN else gender
        age = AgeGroup.ADULT if age == AgeGroup.UNKNOWN else age
    elif category == "child":
        age = AgeGroup.CHILD

    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    return GenderAgePrediction(
        gender=gender.value,
        age_group=age.value,
        raw_label=category or None,
        gender_confidence=round(confidence, 4),
        age_confidence=round(confidence, 4),
        source="llm",
    )


class LLMGenderAgeClassifier:
    """Lazily-initialised Gemini client wrapper (process-wide singleton)."""

    def __init__(self) -> None:
        self._client: Any = None
        self._checked = False
        self._lock = threading.Lock()

    @property
    def is_available(self) -> bool:
        if not settings.GENDER_AGE_LLM_FALLBACK or not settings.GEMINI_API_KEY:
            return False
        self._ensure_client()
        return self._client is not None

    def _ensure_client(self) -> None:
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
                logger.info("gemini_client_ready", model=settings.GEMINI_MODEL)
            except Exception as exc:  # noqa: BLE001
                logger.warning("gemini_client_unavailable", error=str(exc))
                self._client = None

    def classify(self, wav_bytes: bytes, *, mime_type: str = "audio/wav") -> GenderAgePrediction | None:
        """Classify a single speaker's audio. Returns None on any failure."""
        if not wav_bytes or not self.is_available:
            return None
        try:
            from google.genai import types

            response = self._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=wav_bytes, mime_type=mime_type),
                    _PROMPT,
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            payload = _extract_json(getattr(response, "text", "") or "")
            if not payload:
                logger.warning("gemini_unparsable_response")
                return None
            result = _interpret(payload)
            logger.info(
                "gemini_gender_age",
                gender=result.gender,
                age_group=result.age_group,
                confidence=result.gender_confidence,
            )
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("gemini_classify_failed", error=str(exc))
            return None


# --------------------------------------------------------------- singleton
_instance: LLMGenderAgeClassifier | None = None
_instance_lock = threading.Lock()


def get_llm_gender_age_classifier() -> LLMGenderAgeClassifier:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = LLMGenderAgeClassifier()
    return _instance
