"""Hugging Face wav2vec2 gender & age-group classification service.

Wraps two independent ``transformers`` audio-classification pipelines:

* Gender : ``alefiury/wav2vec2-large-xlsr-53-gender-recognition-librispeech``
* Age    : ``anantoj/wav2vec2-xls-r-300m-adult-child-cls``

Both models consume a 16 kHz, mono, float32 waveform — exactly what the
pipeline already produces for each diarized speaker — so no extra audio
plumbing is required.

Design notes
------------
* This service is **append-only** and fully independent of the existing
  scikit-learn ``gender_age_clf`` model and the Gemini fallback. It produces
  the same :class:`GenderAgePrediction` dataclass the rest of the system
  already consumes (DB persistence, API schema, PDF report) — only the
  ``source`` field is set to ``"hf"``.
* It degrades gracefully: if disabled, if ``transformers`` is unavailable, or
  if a model fails to download/load, :meth:`predict` returns ``None`` and the
  caller falls back to the legacy path. Nothing breaks.
* Models are downloaded once into ``HF_HOME`` (a persistent Docker volume) and
  loaded a single time per process (lazy, thread-safe).
"""

from __future__ import annotations

import threading
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.models.enums import AgeGroup, Gender
from app.services.ml.types import GenderAgePrediction

logger = get_logger(__name__)


def _map_gender(label: str) -> Gender:
    """Map a raw gender-model label onto the domain :class:`Gender`."""
    key = (label or "").strip().lower()
    if "female" in key or key in {"f", "woman", "women"}:
        return Gender.FEMALE
    if "male" in key or key in {"m", "man", "men"}:
        return Gender.MALE
    return Gender.UNKNOWN


def _map_age(label: str) -> AgeGroup:
    """Map a raw age-model label onto the domain :class:`AgeGroup`.

    The configured age model distinguishes adult vs child; the extra teen /
    senior tokens are handled defensively so a richer replacement model would
    map cleanly without code changes.
    """
    key = (label or "").strip().lower()
    if "child" in key or "kid" in key or "infant" in key:
        return AgeGroup.CHILD
    if "teen" in key or "adolesc" in key or "youth" in key:
        return AgeGroup.TEEN
    if "senior" in key or "elder" in key or "old" in key:
        return AgeGroup.SENIOR
    if "adult" in key:
        return AgeGroup.ADULT
    return AgeGroup.UNKNOWN


class HFGenderAgeClassifier:
    """Lazily-initialised wrapper around the two wav2vec2 pipelines.

    Process-wide singleton (see :func:`get_hf_gender_age_classifier`).
    """

    def __init__(self) -> None:
        self._gender_pipe: Any = None
        self._age_pipe: Any = None
        self._checked = False
        self._ok = False
        self._lock = threading.Lock()

    # ----------------------------------------------------------- availability
    @property
    def is_enabled(self) -> bool:
        """Whether the feature flag is on (cheap; no model loading)."""
        return bool(settings.GENDER_AGE_HF_ENABLED)

    @property
    def is_available(self) -> bool:
        """True once both pipelines have loaded successfully.

        Triggers a one-time lazy load. On any failure this stays False and the
        caller falls back to the legacy gender/age path.
        """
        if not self.is_enabled:
            return False
        self.load()
        return self._ok

    # ------------------------------------------------------------------- load
    def _select_device(self) -> int:
        """transformers device index: -1 = CPU, 0 = first CUDA device."""
        pref = settings.GENDER_AGE_HF_DEVICE
        if pref == "cpu":
            return -1
        try:
            import torch

            return 0 if torch.cuda.is_available() else -1
        except Exception:  # noqa: BLE001
            return -1

    def load(self) -> None:
        """Construct both pipelines once. Never raises — failures disable HF."""
        if self._checked:
            return
        with self._lock:
            if self._checked:
                return
            self._checked = True
            if not self.is_enabled:
                logger.info("hf_gender_age_disabled")
                return
            try:
                from transformers import pipeline

                device = self._select_device()
                token = settings.HUGGINGFACE_TOKEN
                logger.info(
                    "hf_gender_age_load",
                    gender_model=settings.GENDER_MODEL_ID,
                    age_model=settings.AGE_MODEL_ID,
                    device=device,
                )
                self._gender_pipe = pipeline(
                    "audio-classification",
                    model=settings.GENDER_MODEL_ID,
                    device=device,
                    token=token,
                )
                self._age_pipe = pipeline(
                    "audio-classification",
                    model=settings.AGE_MODEL_ID,
                    device=device,
                    token=token,
                )
                self._ok = True
                logger.info("hf_gender_age_ready")
            except Exception as exc:  # noqa: BLE001
                logger.warning("hf_gender_age_unavailable", error=str(exc))
                self._gender_pipe = None
                self._age_pipe = None
                self._ok = False

    @property
    def is_loaded(self) -> bool:
        return self._ok

    # --------------------------------------------------------------- predict
    @staticmethod
    def _top(pipe: Any, arr: Any, sr: int) -> tuple[str, float]:
        """Run a pipeline and return the (label, score) of the top class."""
        preds = pipe({"raw": arr, "sampling_rate": sr})
        if isinstance(preds, dict):
            preds = [preds]
        best = max(preds, key=lambda p: float(p.get("score", 0.0)))
        return str(best.get("label", "")), float(best.get("score", 0.0))

    def predict(self, samples: Any, sr: int) -> GenderAgePrediction | None:
        """Predict gender + age for one speaker's 16 kHz float32 waveform.

        Returns ``None`` if the service is unavailable or inference fails, so
        the caller can fall back to the legacy gender/age path.
        """
        if not self.is_available:
            return None

        import numpy as np

        arr = np.asarray(samples, dtype=np.float32)
        max_s = settings.GENDER_AGE_HF_MAX_SECONDS
        if max_s and sr > 0:
            limit = int(max_s * sr)
            if 0 < limit < arr.size:
                arr = arr[:limit]
        if arr.size == 0:
            return None

        try:
            g_label, g_score = self._top(self._gender_pipe, arr, sr)
            a_label, a_score = self._top(self._age_pipe, arr, sr)
        except Exception as exc:  # noqa: BLE001
            logger.warning("hf_gender_age_predict_failed", error=str(exc))
            return None

        gender = _map_gender(g_label)
        age = _map_age(a_label)
        logger.info(
            "hf_gender_age",
            gender=gender.value,
            age_group=age.value,
            gender_label=g_label,
            age_label=a_label,
        )
        return GenderAgePrediction(
            gender=gender.value,
            age_group=age.value,
            raw_label=f"{g_label}|{a_label}"[:64],
            gender_confidence=round(g_score, 4),
            age_confidence=round(a_score, 4),
            source="hf",
        )


# --------------------------------------------------------------- singleton
_instance: HFGenderAgeClassifier | None = None
_instance_lock = threading.Lock()


def get_hf_gender_age_classifier() -> HFGenderAgeClassifier:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = HFGenderAgeClassifier()
    return _instance
