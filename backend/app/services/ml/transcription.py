"""Speech transcription & translation service (faster-whisper).

Whisper natively supports two tasks:

* ``transcribe`` — emit text in the source language (Kannada).
* ``translate``  — emit English text.

We run both over the same audio and align translated segments to the source
timeline by maximum temporal overlap, yielding segments that carry BOTH the
original Kannada text and its English translation with timestamps.

The model is loaded once and reused across jobs.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.exceptions import ModelInferenceError, PipelineError
from app.core.logging import get_logger
from app.services.ml.types import TranscriptSegment

logger = get_logger(__name__)


def _resolve_device(preference: str) -> str:
    if preference != "auto":
        return preference
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:  # noqa: BLE001
        return "cpu"


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


class TranscriptionService:
    """Wraps a faster-whisper model as a process-wide singleton."""

    def __init__(self) -> None:
        self._model: Any = None
        self._device: str = "cpu"
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            try:
                from faster_whisper import WhisperModel

                self._device = _resolve_device(settings.WHISPER_DEVICE)
                compute_type = (
                    settings.WHISPER_COMPUTE_TYPE if self._device == "cpu" else "float16"
                )
                logger.info(
                    "whisper_model_load",
                    size=settings.WHISPER_MODEL_SIZE,
                    device=self._device,
                    compute_type=compute_type,
                )
                self._model = WhisperModel(
                    settings.WHISPER_MODEL_SIZE,
                    device=self._device,
                    compute_type=compute_type,
                )
                logger.info("whisper_model_ready", device=self._device)
            except Exception as exc:  # noqa: BLE001
                raise ModelInferenceError(
                    f"Failed to load Whisper model: {exc}", code="whisper_load_failed"
                ) from exc

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    # ------------------------------------------------------------- internal
    def _run(self, audio_path: str | Path, task: str) -> list[tuple[float, float, str, float | None]]:
        language = settings.TRANSCRIPTION_SOURCE_LANGUAGE
        segments, _info = self._model.transcribe(
            str(audio_path),
            task=task,
            language=language,
            vad_filter=True,
            beam_size=5,
        )
        out: list[tuple[float, float, str, float | None]] = []
        for seg in segments:
            prob = getattr(seg, "avg_logprob", None)
            conf = None
            if prob is not None:
                import math

                conf = round(1.0 / (1.0 + math.exp(-prob)), 4)
            out.append((float(seg.start), float(seg.end), seg.text.strip(), conf))
        return out

    # ------------------------------------------------------------- transcribe
    def transcribe(self, audio_path: str | Path) -> list[TranscriptSegment]:
        """Return timestamped segments with Kannada source + English translation."""
        self.load()
        try:
            source = self._run(audio_path, task="transcribe")
            translated = self._run(audio_path, task="translate")
        except Exception as exc:  # noqa: BLE001
            raise PipelineError(
                f"Transcription failed: {exc}", code="transcription_failed"
            ) from exc

        segments: list[TranscriptSegment] = []
        for start, end, text_src, conf in source:
            # Find the English segment with the greatest temporal overlap.
            best_text = ""
            best_ov = 0.0
            for t_start, t_end, t_text, _ in translated:
                ov = _overlap(start, end, t_start, t_end)
                if ov > best_ov:
                    best_ov, best_text = ov, t_text
            segments.append(
                TranscriptSegment(
                    start=start,
                    end=end,
                    speaker="",  # assigned later by the pipeline
                    text_source=text_src,
                    text_translated=best_text,
                    confidence=conf,
                )
            )
        logger.info("transcription_complete", segments=len(segments))
        return segments


# --------------------------------------------------------------- singleton
_instance: TranscriptionService | None = None
_instance_lock = threading.Lock()


def get_transcription_service() -> TranscriptionService:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = TranscriptionService()
    return _instance
