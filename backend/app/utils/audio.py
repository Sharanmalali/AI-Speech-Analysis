"""Audio I/O and preprocessing helpers.

Thin, dependency-lazy wrappers around ``librosa``/``soundfile``/``noisereduce``
so the rest of the codebase deals in plain numpy arrays + sample rates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from app.core.exceptions import FileValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class AudioMeta:
    duration_seconds: float
    sample_rate: int
    channels: int


def probe(path: str | Path) -> AudioMeta:
    """Return duration/sample-rate/channels without loading the full signal."""
    import soundfile as sf

    try:
        info = sf.info(str(path))
        return AudioMeta(
            duration_seconds=float(info.frames) / float(info.samplerate),
            sample_rate=int(info.samplerate),
            channels=int(info.channels),
        )
    except Exception as exc:  # noqa: BLE001
        # Fallback to librosa (handles formats soundfile can't, via audioread).
        try:
            import librosa

            duration = float(librosa.get_duration(path=str(path)))
            sr = int(librosa.get_samplerate(str(path)))
            return AudioMeta(duration_seconds=duration, sample_rate=sr, channels=1)
        except Exception as inner:  # noqa: BLE001
            raise FileValidationError(
                f"Could not read audio metadata: {inner}", code="audio_unreadable"
            ) from exc


def load_audio(
    path: str | Path,
    *,
    target_sr: int | None = None,
    mono: bool = True,
):
    """Load an audio file as a float32 numpy array at ``target_sr``.

    Returns ``(samples, sample_rate)``.
    """
    import librosa

    target_sr = target_sr or settings.TARGET_SAMPLE_RATE
    try:
        samples, sr = librosa.load(str(path), sr=target_sr, mono=mono)
    except Exception as exc:  # noqa: BLE001
        raise FileValidationError(
            f"Could not decode audio file: {exc}", code="audio_decode_failed"
        ) from exc
    return samples, int(sr)


def reduce_noise(samples, sr: int):
    """Apply spectral-gating noise reduction (best-effort)."""
    if not settings.ENABLE_NOISE_REDUCTION:
        return samples
    try:
        import noisereduce as nr

        return nr.reduce_noise(y=samples, sr=sr)
    except Exception as exc:  # noqa: BLE001
        logger.warning("noise_reduction_skipped", error=str(exc))
        return samples


def slice_segment(samples, sr: int, start: float, end: float):
    """Return the sample slice for ``[start, end]`` seconds."""
    lo = max(0, int(start * sr))
    hi = min(len(samples), int(end * sr))
    return samples[lo:hi]


def concat_segments(samples, sr: int, intervals: list[tuple[float, float]]):
    """Concatenate multiple time intervals (seconds) into one signal."""
    import numpy as np

    if not intervals:
        return np.zeros(0, dtype=np.float32)
    chunks = [slice_segment(samples, sr, s, e) for s, e in intervals]
    chunks = [c for c in chunks if len(c) > 0]
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks)


def to_wav_bytes(samples, sr: int, *, max_seconds: float | None = None) -> bytes:
    """Encode a float waveform to in-memory 16-bit PCM WAV bytes.

    Optionally trims to the first ``max_seconds`` (used to keep LLM payloads
    small). Returns an empty bytestring if encoding is unavailable.
    """
    import io

    import numpy as np

    arr = np.asarray(samples, dtype=np.float32)
    if max_seconds is not None and sr > 0:
        limit = int(max_seconds * sr)
        if limit > 0:
            arr = arr[:limit]
    if arr.size == 0:
        return b""

    try:
        import soundfile as sf

        buf = io.BytesIO()
        sf.write(buf, arr, sr, format="WAV", subtype="PCM_16")
        return buf.getvalue()
    except Exception as exc:  # noqa: BLE001
        logger.warning("wav_encode_failed", error=str(exc))
        return b""
