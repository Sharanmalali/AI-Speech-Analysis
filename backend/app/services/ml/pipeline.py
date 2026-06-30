"""End-to-end audio analysis pipeline orchestration.

Coordinates the independent ML services into the full inference flow:

    probe -> load -> noise reduction -> diarization -> segmentation ->
    transcription/translation -> per-speaker feature extraction ->
    gender/age + atypicality prediction -> aggregation

The pipeline owns no model state of its own; it pulls each service from the
registry singletons. A ``progress`` callback lets the Celery task surface
fine-grained stage/percentage updates to the database and UI.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from app.config import settings
from app.core.exceptions import PipelineError
from app.core.logging import get_logger
from app.models.enums import JobStage
from app.services.ml.atypicality_classifier import get_atypicality_classifier
from app.services.ml.feature_extraction import extract_features
from app.services.ml.gender_age_classifier import get_gender_age_classifier
from app.services.ml.hf_gender_age import get_hf_gender_age_classifier
from app.services.ml.llm_gender_age import get_llm_gender_age_classifier
from app.services.ml.speaker_diarization import get_diarization_service
from app.services.ml.transcription import get_transcription_service
from app.services.ml.types import (
    DiarizationSegment,
    PipelineResult,
    SpeakerResult,
    TranscriptSegment,
)
from app.utils import audio as audio_utils

logger = get_logger(__name__)

ProgressCallback = Callable[[JobStage, float], None]

# Distinct, accessible colours assigned to speakers in order of appearance.
SPEAKER_COLORS: tuple[str, ...] = (
    "#6366F1",  # indigo
    "#EC4899",  # pink
    "#10B981",  # emerald
    "#F59E0B",  # amber
    "#3B82F6",  # blue
    "#8B5CF6",  # violet
    "#EF4444",  # red
    "#14B8A6",  # teal
    "#F97316",  # orange
    "#A855F7",  # purple
)


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _assign_speakers(
    transcript: list[TranscriptSegment], diarization: list[DiarizationSegment]
) -> None:
    """Attach the best-overlapping diarization speaker to each transcript segment."""
    for seg in transcript:
        best_speaker = ""
        best_ov = 0.0
        for d in diarization:
            ov = _overlap(seg.start, seg.end, d.start, d.end)
            if ov > best_ov:
                best_ov, best_speaker = ov, d.speaker
        seg.speaker = best_speaker


def _label_for_index(index: int) -> str:
    """0 -> 'A', 1 -> 'B', ... 25 -> 'Z', 26 -> 'AA'."""
    label = ""
    n = index
    while True:
        label = chr(ord("A") + (n % 26)) + label
        n = n // 26 - 1
        if n < 0:
            break
    return label


class AudioAnalysisPipeline:
    """Runs the full analysis for a single audio file."""

    def __init__(self, progress: ProgressCallback | None = None) -> None:
        self._progress = progress
        self._diarizer = get_diarization_service()
        self._transcriber = get_transcription_service()
        self._gender_age = get_gender_age_classifier()
        self._atypicality = get_atypicality_classifier()
        self._llm_gender_age = get_llm_gender_age_classifier()
        self._hf_gender_age = get_hf_gender_age_classifier()

    def _emit(self, stage: JobStage, pct: float) -> None:
        if self._progress is not None:
            try:
                self._progress(stage, round(pct, 2))
            except Exception as exc:  # noqa: BLE001
                logger.warning("progress_callback_failed", error=str(exc))

    def _predict_gender_age(self, features, speaker_audio, sr: int):
        """Predict gender/age, preferring the HF wav2vec2 models.

        Resolution order (each step falls back on failure / unavailability):
          1. Dedicated Hugging Face wav2vec2 gender + age models (primary).
          2. Legacy scikit-learn ``gender_age_clf`` model.
          3. Gemini audio fallback for any field still "unknown".

        This keeps the new models as the primary source while preserving the
        existing behaviour intact whenever they are disabled or unavailable.
        """
        if self._hf_gender_age.is_available:
            try:
                hf_pred = self._hf_gender_age.predict(speaker_audio, sr)
            except Exception as exc:  # noqa: BLE001
                logger.warning("hf_gender_age_failed", error=str(exc))
                hf_pred = None
            if hf_pred is not None:
                # Top up any residual "unknown" via the existing LLM fallback.
                return self._maybe_llm_fallback(hf_pred, speaker_audio, sr)

        # Legacy path (unchanged): sklearn model + optional Gemini fallback.
        prediction = self._gender_age.predict(features)
        return self._maybe_llm_fallback(prediction, speaker_audio, sr)

    def _maybe_llm_fallback(self, prediction, speaker_audio, sr: int):
        """If the local model was uninformative, try the Gemini audio fallback.

        Triggers when gender OR age group is "unknown" and the LLM fallback is
        available. On any failure the original prediction is returned unchanged.
        """
        needs_help = prediction.gender == "unknown" or prediction.age_group == "unknown"
        if not needs_help or not self._llm_gender_age.is_available:
            return prediction
        try:
            wav = audio_utils.to_wav_bytes(
                speaker_audio, sr, max_seconds=settings.LLM_AUDIO_MAX_SECONDS
            )
            llm_result = self._llm_gender_age.classify(wav)
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_fallback_failed", error=str(exc))
            return prediction
        if llm_result is None:
            return prediction
        logger.info("llm_fallback_applied", gender=llm_result.gender, age=llm_result.age_group)
        return llm_result

    # ------------------------------------------------------------------- run
    def run(self, audio_path: str | Path) -> PipelineResult:
        start_time = time.perf_counter()
        audio_path = str(audio_path)

        # 1. Probe + load -----------------------------------------------------
        self._emit(JobStage.UPLOADED, 2.0)
        meta = audio_utils.probe(audio_path)
        samples, sr = audio_utils.load_audio(audio_path, target_sr=settings.TARGET_SAMPLE_RATE)

        # 2. Noise reduction --------------------------------------------------
        self._emit(JobStage.NOISE_REDUCTION, 10.0)
        samples = audio_utils.reduce_noise(samples, sr)

        # 3. Diarization ------------------------------------------------------
        self._emit(JobStage.DIARIZATION, 20.0)
        diarization = self._diarizer.diarize(audio_path)
        if not diarization:
            raise PipelineError("No speech detected during diarization.", code="no_speech")

        # 4. Transcription + translation -------------------------------------
        self._emit(JobStage.TRANSCRIPTION, 45.0)
        transcript = self._transcriber.transcribe(audio_path)

        # 5. Segmentation: assign speakers to transcript segments ------------
        self._emit(JobStage.SEGMENTATION, 60.0)
        _assign_speakers(transcript, diarization)

        # 6. Group by diarization speaker, ordered by first appearance -------
        order: list[str] = []
        for d in sorted(diarization, key=lambda s: s.start):
            if d.speaker not in order:
                order.append(d.speaker)

        diar_by_speaker: dict[str, list[DiarizationSegment]] = {s: [] for s in order}
        for d in diarization:
            diar_by_speaker.setdefault(d.speaker, []).append(d)

        trans_by_speaker: dict[str, list[TranscriptSegment]] = {s: [] for s in order}
        for seg in transcript:
            if seg.speaker in trans_by_speaker:
                trans_by_speaker[seg.speaker].append(seg)
            elif seg.speaker:
                trans_by_speaker.setdefault(seg.speaker, []).append(seg)
                if seg.speaker not in order:
                    order.append(seg.speaker)

        # 7. Per-speaker feature extraction + predictions --------------------
        speakers: list[SpeakerResult] = []
        n = max(1, len(order))
        for idx, diar_id in enumerate(order):
            base_pct = 65.0 + (idx / n) * 30.0
            self._emit(JobStage.FEATURE_EXTRACTION, base_pct)

            d_segs = sorted(diar_by_speaker.get(diar_id, []), key=lambda s: s.start)
            t_segs = sorted(trans_by_speaker.get(diar_id, []), key=lambda s: s.start)

            intervals = [(d.start, d.end) for d in d_segs]
            total_speech = sum(d.duration for d in d_segs)
            first_onset = d_segs[0].start if d_segs else 0.0
            # Pauses = gaps between consecutive segments of this speaker.
            total_pause = 0.0
            for prev, nxt in zip(d_segs, d_segs[1:]):
                total_pause += max(0.0, nxt.start - prev.end)
            pause_ratio = (total_pause / total_speech) if total_speech > 0 else 0.0
            word_count = sum(len(s.text_translated.split()) for s in t_segs)
            speech_rate = (word_count / total_speech) if total_speech > 0 else 0.0

            speaker_audio = audio_utils.concat_segments(samples, sr, intervals)

            features = extract_features(
                speaker_audio,
                sr,
                latency_to_speak_sec=first_onset,
                pause_to_speech_ratio=pause_ratio,
                speech_rate=speech_rate,
            )

            self._emit(JobStage.GENDER_PREDICTION, base_pct + 10.0 / n)
            gender_age = self._predict_gender_age(features, speaker_audio, sr)

            self._emit(JobStage.ATYPICALITY_CLASSIFICATION, base_pct + 20.0 / n)
            atypicality = self._atypicality.predict(features)

            speakers.append(
                SpeakerResult(
                    label=_label_for_index(idx),
                    diarization_id=diar_id,
                    color=SPEAKER_COLORS[idx % len(SPEAKER_COLORS)],
                    total_speech_seconds=round(total_speech, 3),
                    total_pause_seconds=round(total_pause, 3),
                    segment_count=len(d_segs),
                    word_count=word_count,
                    segments=t_segs,
                    features=features,
                    gender_age=gender_age,
                    atypicality=atypicality,
                )
            )

        # 8. Aggregate --------------------------------------------------------
        self._emit(JobStage.AGGREGATION, 97.0)
        elapsed = time.perf_counter() - start_time
        result = PipelineResult(
            duration_seconds=round(meta.duration_seconds, 3),
            sample_rate=sr,
            detected_speakers=len(order),
            speakers=speakers,
            language_source=settings.TRANSCRIPTION_SOURCE_LANGUAGE,
            language_target=settings.TRANSCRIPTION_TARGET_LANGUAGE,
            processing_time_seconds=round(elapsed, 3),
        )
        self._emit(JobStage.DONE, 100.0)
        logger.info(
            "pipeline_complete",
            speakers=result.detected_speakers,
            duration=result.duration_seconds,
            elapsed=result.processing_time_seconds,
        )
        return result


def run_pipeline(audio_path: str | Path, progress: ProgressCallback | None = None) -> PipelineResult:
    """Convenience wrapper to run a one-off pipeline."""
    return AudioAnalysisPipeline(progress=progress).run(audio_path)
