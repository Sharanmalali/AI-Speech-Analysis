"""Internal data contracts shared across the ML services and pipeline.

Plain dataclasses are used (rather than Pydantic) for the hot inference path
to minimise overhead. They are converted to Pydantic response schemas at the
API boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DiarizationSegment:
    """A contiguous span of speech attributed to one speaker."""

    speaker: str          # diarization id, e.g. "SPEAKER_00"
    start: float          # seconds
    end: float            # seconds

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(slots=True)
class TranscriptSegment:
    """A transcribed (and translated) utterance with timing + speaker."""

    start: float
    end: float
    speaker: str
    text_source: str = ""        # original language (Kannada)
    text_translated: str = ""    # English translation
    confidence: float | None = None

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(slots=True)
class AcousticFeatures:
    """Acoustic features for a single speaker.

    The first seven map 1:1 to the atypicality model's expected inputs.
    ``gender_age_vector`` is the 483-dim input for the gender/age classifier.
    """

    latency_to_speak_sec: float
    pause_to_speech_ratio: float
    pronunciation_flux_var: float
    f0_mean: float
    jitter: float
    shimmer: float
    hnr: float
    # Optional extras retained for transparency / the report.
    f0_std: float = 0.0
    speech_rate: float = 0.0
    gender_age_vector: list[float] = field(default_factory=list)

    def atypicality_row(self) -> list[float]:
        """Return the 7 features in the exact order the scaler expects."""
        return [
            self.latency_to_speak_sec,
            self.pause_to_speech_ratio,
            self.pronunciation_flux_var,
            self.f0_mean,
            self.jitter,
            self.shimmer,
            self.hnr,
        ]

    def as_dict(self) -> dict[str, float]:
        return {
            "latency_to_speak_sec": self.latency_to_speak_sec,
            "pause_to_speech_ratio": self.pause_to_speech_ratio,
            "pronunciation_flux_var": self.pronunciation_flux_var,
            "f0_mean": self.f0_mean,
            "jitter": self.jitter,
            "shimmer": self.shimmer,
            "hnr": self.hnr,
            "f0_std": self.f0_std,
            "speech_rate": self.speech_rate,
        }


@dataclass(slots=True)
class GenderAgePrediction:
    gender: str                       # "male" | "female" | "unknown"
    age_group: str                    # "child" | "teen" | "adult" | "senior" | "unknown"
    raw_label: str | None = None
    gender_confidence: float | None = None
    age_confidence: float | None = None
    source: str = "model"             # "model" | "hf" | "llm"


@dataclass(slots=True)
class AtypicalityPrediction:
    label: str                        # "typical" | "atypical" | "unknown"
    score: float                      # IsolationForest decision_function output
    confidence: float | None = None


@dataclass(slots=True)
class SpeakerResult:
    """Fully aggregated per-speaker result."""

    label: str                        # "A", "B", ...
    diarization_id: str
    color: str
    total_speech_seconds: float
    total_pause_seconds: float
    segment_count: int
    word_count: int
    segments: list[TranscriptSegment]
    features: AcousticFeatures | None
    gender_age: GenderAgePrediction | None
    atypicality: AtypicalityPrediction | None


@dataclass(slots=True)
class PipelineResult:
    """Top-level pipeline output for a single audio file."""

    duration_seconds: float
    sample_rate: int
    detected_speakers: int
    speakers: list[SpeakerResult]
    language_source: str
    language_target: str
    processing_time_seconds: float
