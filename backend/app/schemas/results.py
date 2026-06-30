"""Result schemas: speakers, transcriptions, predictions and full results."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.models.enums import AgeGroup, AtypicalityLabel, Gender, JobStatus
from app.schemas.common import ORMModel


class TranscriptionRead(ORMModel):
    id: uuid.UUID
    start_time: float
    end_time: float
    text_source: str | None
    text_translated: str | None
    confidence: float | None


class PredictionRead(ORMModel):
    gender: Gender
    gender_confidence: float | None
    age_group: AgeGroup
    age_confidence: float | None
    raw_class_label: str | None
    gender_age_source: str = "model"
    atypicality: AtypicalityLabel
    atypicality_score: float | None
    atypicality_confidence: float | None
    features: dict | None


class SpeakerRead(ORMModel):
    id: uuid.UUID
    label: str
    diarization_id: str
    color: str | None
    total_speech_seconds: float
    total_pause_seconds: float
    segment_count: int
    word_count: int
    prediction: PredictionRead | None
    transcriptions: list[TranscriptionRead]


class AudioSummary(BaseModel):
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    original_filename: str


class ResultResponse(BaseModel):
    """The complete analysis result for a job, consumed by the dashboard."""

    job_id: uuid.UUID
    status: JobStatus
    detected_speakers: int
    language_source: str
    language_target: str
    processing_time_seconds: float | None
    audio: AudioSummary
    speakers: list[SpeakerRead]
    has_report: bool = False
