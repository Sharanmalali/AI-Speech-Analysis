"""Speaker diarization service (pyannote.audio).

Loads the ``pyannote/speaker-diarization-3.1`` pipeline exactly once at
startup (it is expensive to initialise) and reuses it for every job. A
Hugging Face access token is required because the model is gated.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.exceptions import ModelInferenceError, PipelineError
from app.core.logging import get_logger
from app.services.ml.types import DiarizationSegment

logger = get_logger(__name__)


def _resolve_device(preference: str) -> str:
    """Resolve 'auto' to 'cuda' when available, else 'cpu'."""
    if preference != "auto":
        return preference
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:  # noqa: BLE001
        return "cpu"


class SpeakerDiarizationService:
    """Wraps the pyannote diarization pipeline as a process-wide singleton."""

    def __init__(self) -> None:
        self._pipeline: Any = None
        self._device: str = "cpu"
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        if self._pipeline is not None:
            return
        with self._lock:
            if self._pipeline is not None:
                return
            if not settings.HUGGINGFACE_TOKEN:
                raise ModelInferenceError(
                    "HUGGINGFACE_TOKEN is required to load the pyannote pipeline.",
                    code="hf_token_missing",
                )
            try:
                import torch
                from pyannote.audio import Pipeline

                self._device = _resolve_device(settings.DIARIZATION_DEVICE)
                logger.info(
                    "diarization_pipeline_load",
                    pipeline=settings.PYANNOTE_PIPELINE,
                    device=self._device,
                )
                pipeline = Pipeline.from_pretrained(
                    settings.PYANNOTE_PIPELINE,
                    use_auth_token=settings.HUGGINGFACE_TOKEN,
                )
                pipeline.to(torch.device(self._device))
                self._pipeline = pipeline
                logger.info("diarization_pipeline_ready", device=self._device)
            except Exception as exc:  # noqa: BLE001
                raise ModelInferenceError(
                    f"Failed to load diarization pipeline: {exc}",
                    code="diarization_load_failed",
                ) from exc

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    # ------------------------------------------------------------- diarize
    def diarize(
        self,
        audio_path: str | Path,
        *,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
    ) -> list[DiarizationSegment]:
        """Run diarization and return time-ordered speaker segments."""
        self.load()
        kwargs: dict[str, int] = {}
        min_s = min_speakers if min_speakers is not None else settings.MIN_SPEAKERS
        max_s = max_speakers if max_speakers is not None else settings.MAX_SPEAKERS
        if min_s is not None:
            kwargs["min_speakers"] = min_s
        if max_s is not None:
            kwargs["max_speakers"] = max_s

        try:
            annotation = self._pipeline(str(audio_path), **kwargs)
        except Exception as exc:  # noqa: BLE001
            raise PipelineError(f"Diarization failed: {exc}", code="diarization_failed") from exc

        segments: list[DiarizationSegment] = [
            DiarizationSegment(speaker=str(speaker), start=float(turn.start), end=float(turn.end))
            for turn, _, speaker in annotation.itertracks(yield_label=True)
        ]
        segments.sort(key=lambda s: s.start)
        logger.info(
            "diarization_complete",
            segments=len(segments),
            speakers=len({s.speaker for s in segments}),
        )
        return segments


# --------------------------------------------------------------- singleton
_instance: SpeakerDiarizationService | None = None
_instance_lock = threading.Lock()


def get_diarization_service() -> SpeakerDiarizationService:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = SpeakerDiarizationService()
    return _instance
