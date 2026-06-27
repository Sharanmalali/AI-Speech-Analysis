"""Acoustic feature extraction.

Produces the inputs required by both downstream models from a speaker's
audio samples:

* The **7 atypicality features** (exact names/order expected by the scaler):
  ``latency_to_speak_sec, pause_to_speech_ratio, pronunciation_flux_var,
  f0_mean, jitter, shimmer, hnr``.

* The **480-dim gender/age vector** — a deterministic, documented summary of
  a log-mel spectrogram (``N_MELS`` mel bands x ``N_FRAMES`` pooled time
  frames, flattened). This is a *reconstruction* of the original model's
  unnamed numeric features; if the original training feature pipeline is
  shared, only this function needs to change to match it.

Heavy audio libraries (``librosa``, ``parselmouth``) are imported lazily so
the module can be imported in environments without the full audio stack
(e.g. unit tests of the sklearn services).
"""

from __future__ import annotations

from app.config import settings
from app.core.logging import get_logger
from app.services.ml.types import AcousticFeatures

logger = get_logger(__name__)

# --- Gender/age vector geometry (480 = N_MELS * N_FRAMES) ------------------
N_MELS = 40
N_FRAMES = 12
GENDER_AGE_VECTOR_LEN = N_MELS * N_FRAMES  # 480


def _safe(value: float, default: float = 0.0) -> float:
    """Coerce NaN/inf to a finite default."""
    import math

    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(v) or math.isinf(v):
        return default
    return v


def _log_mel_summary(samples, sr: int) -> list[float]:
    """Return a flattened (N_MELS x N_FRAMES) log-mel summary of length 480.

    Time frames are pooled into ``N_FRAMES`` buckets by averaging, giving a
    fixed-length representation independent of clip duration.
    """
    import numpy as np

    try:
        import librosa

        mel = librosa.feature.melspectrogram(
            y=np.asarray(samples, dtype=np.float32),
            sr=sr,
            n_mels=N_MELS,
            n_fft=2048,
            hop_length=512,
        )
        log_mel = librosa.power_to_db(mel, ref=np.max)  # (N_MELS, T)
    except Exception as exc:  # noqa: BLE001
        logger.warning("log_mel_failed", error=str(exc))
        return [0.0] * GENDER_AGE_VECTOR_LEN

    t = log_mel.shape[1]
    if t == 0:
        return [0.0] * GENDER_AGE_VECTOR_LEN

    # Pool the time axis into exactly N_FRAMES columns.
    idx = np.linspace(0, t, num=N_FRAMES + 1, dtype=int)
    pooled = np.zeros((N_MELS, N_FRAMES), dtype=np.float32)
    for i in range(N_FRAMES):
        lo, hi = idx[i], max(idx[i] + 1, idx[i + 1])
        pooled[:, i] = log_mel[:, lo:hi].mean(axis=1)

    return [float(v) for v in pooled.flatten()]


def _spectral_flux_variance(samples, sr: int) -> float:
    """Variance of frame-to-frame spectral flux — a pronunciation-flux proxy."""
    import numpy as np

    try:
        import librosa

        S = np.abs(librosa.stft(np.asarray(samples, dtype=np.float32), n_fft=1024, hop_length=256))
        # Normalise per frame, then L2 of positive differences across time.
        norm = S / (S.sum(axis=0, keepdims=True) + 1e-9)
        diff = np.diff(norm, axis=1)
        flux = np.sqrt((np.clip(diff, 0, None) ** 2).sum(axis=0))
        return _safe(float(np.var(flux)))
    except Exception as exc:  # noqa: BLE001
        logger.warning("spectral_flux_failed", error=str(exc))
        return 0.0


def _voice_quality(samples, sr: int) -> tuple[float, float, float, float, float]:
    """Return (f0_mean, f0_std, jitter, shimmer, hnr) via Praat/parselmouth."""
    import numpy as np

    try:
        import parselmouth
        from parselmouth.praat import call

        snd = parselmouth.Sound(np.asarray(samples, dtype=np.float64), sampling_frequency=sr)
        pitch = snd.to_pitch()
        f0_values = pitch.selected_array["frequency"]
        voiced = f0_values[f0_values > 0]
        f0_mean = _safe(float(np.mean(voiced))) if voiced.size else 0.0
        f0_std = _safe(float(np.std(voiced))) if voiced.size else 0.0

        point_process = call(snd, "To PointProcess (periodic, cc)", 75, 600)
        jitter = _safe(
            call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        )
        shimmer = _safe(
            call(
                [snd, point_process],
                "Get shimmer (local)",
                0, 0, 0.0001, 0.02, 1.3, 1.6,
            )
        )
        harmonicity = snd.to_harmonicity()
        hnr_vals = harmonicity.values[harmonicity.values != -200]
        hnr = _safe(float(np.mean(hnr_vals))) if hnr_vals.size else 0.0
        return f0_mean, f0_std, jitter, shimmer, hnr
    except Exception as exc:  # noqa: BLE001
        logger.warning("voice_quality_failed", error=str(exc))
        return 0.0, 0.0, 0.0, 0.0, 0.0


def _estimate_leading_silence(samples, sr: int) -> float:
    """Seconds of leading near-silence before voiced onset (latency proxy)."""
    import numpy as np

    try:
        import librosa

        y = np.asarray(samples, dtype=np.float32)
        intervals = librosa.effects.split(y, top_db=30)
        if len(intervals) == 0:
            return 0.0
        return _safe(float(intervals[0][0]) / sr)
    except Exception as exc:  # noqa: BLE001
        logger.warning("leading_silence_failed", error=str(exc))
        return 0.0


def extract_features(
    samples,
    sr: int | None = None,
    *,
    latency_to_speak_sec: float | None = None,
    pause_to_speech_ratio: float | None = None,
    speech_rate: float = 0.0,
) -> AcousticFeatures:
    """Extract all acoustic features for a speaker's concatenated audio.

    Timing-derived features (``latency_to_speak_sec`` and
    ``pause_to_speech_ratio``) are normally computed from diarization by the
    pipeline and passed in. When omitted, sensible audio-derived fallbacks are
    used so the function is usable standalone.
    """
    sr = sr or settings.TARGET_SAMPLE_RATE

    f0_mean, f0_std, jitter, shimmer, hnr = _voice_quality(samples, sr)
    flux_var = _spectral_flux_variance(samples, sr)
    gender_age_vector = _log_mel_summary(samples, sr)

    if latency_to_speak_sec is None:
        latency_to_speak_sec = _estimate_leading_silence(samples, sr)
    if pause_to_speech_ratio is None:
        pause_to_speech_ratio = 0.0

    return AcousticFeatures(
        latency_to_speak_sec=round(_safe(latency_to_speak_sec), 6),
        pause_to_speech_ratio=round(_safe(pause_to_speech_ratio), 6),
        pronunciation_flux_var=round(flux_var, 6),
        f0_mean=round(f0_mean, 6),
        jitter=round(jitter, 6),
        shimmer=round(shimmer, 6),
        hnr=round(hnr, 6),
        f0_std=round(f0_std, 6),
        speech_rate=round(_safe(speech_rate), 6),
        gender_age_vector=gender_age_vector,
    )
