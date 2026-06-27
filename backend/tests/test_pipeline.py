"""Pipeline orchestration tests with mocked heavy services."""

import numpy as np
import pytest

import app.services.ml.pipeline as pl
from app.services.ml.pipeline import _assign_speakers, _label_for_index
from app.services.ml.types import (
    AcousticFeatures,
    AtypicalityPrediction,
    DiarizationSegment,
    GenderAgePrediction,
    TranscriptSegment,
)
from app.utils.audio import AudioMeta

pytestmark = pytest.mark.unit


def test_label_for_index():
    assert _label_for_index(0) == "A"
    assert _label_for_index(25) == "Z"
    assert _label_for_index(26) == "AA"


def test_assign_speakers_by_overlap():
    diar = [DiarizationSegment("S0", 0, 3), DiarizationSegment("S1", 3, 6)]
    trans = [TranscriptSegment(0.1, 2.9, "", "k", "hello"), TranscriptSegment(3.1, 5.9, "", "k", "hi")]
    _assign_speakers(trans, diar)
    assert trans[0].speaker == "S0"
    assert trans[1].speaker == "S1"


def test_full_pipeline_with_mocks(monkeypatch):
    monkeypatch.setattr(pl.audio_utils, "probe",
                        lambda p: AudioMeta(duration_seconds=9.0, sample_rate=16000, channels=1))
    monkeypatch.setattr(pl.audio_utils, "load_audio",
                        lambda p, target_sr=None, mono=True: (np.zeros(16000 * 9, dtype=np.float32), 16000))
    monkeypatch.setattr(pl.audio_utils, "reduce_noise", lambda s, sr: s)
    monkeypatch.setattr(pl.audio_utils, "concat_segments",
                        lambda s, sr, intervals: np.zeros(1600, dtype=np.float32))
    monkeypatch.setattr(
        pl, "extract_features",
        lambda *a, **k: AcousticFeatures(1.0, 0.5, 4.0, 200.0, 0.02, 0.1, 13.0, gender_age_vector=[0.1] * 480),
    )

    class FakeDiar:
        def diarize(self, path, **k):
            return [
                DiarizationSegment("SPEAKER_00", 0.0, 3.0),
                DiarizationSegment("SPEAKER_01", 3.2, 6.0),
                DiarizationSegment("SPEAKER_00", 6.5, 9.0),
            ]

    class FakeTrans:
        def transcribe(self, path):
            return [
                TranscriptSegment(0.0, 3.0, "", "ನಮಸ್ಕಾರ", "Hello", 0.9),
                TranscriptSegment(3.2, 6.0, "", "ಹೇಗಿದ್ದೀರಿ", "How are you", 0.8),
                TranscriptSegment(6.5, 9.0, "", "ಚೆನ್ನಾಗಿದೆ", "I am fine", 0.85),
            ]

    class FakeGA:
        def predict(self, f):
            return GenderAgePrediction("unknown", "unknown", "0", 1.0, 1.0)

    class FakeHF:
        is_available = False

        def predict(self, samples, sr):  # pragma: no cover - must not be called
            raise AssertionError("HF should not be called when unavailable")

    class FakeAt:
        def predict(self, f):
            return AtypicalityPrediction("typical", 0.12, 0.67)

    p = pl.AudioAnalysisPipeline()
    p._diarizer, p._transcriber, p._gender_age, p._atypicality = FakeDiar(), FakeTrans(), FakeGA(), FakeAt()
    p._hf_gender_age = FakeHF()

    progress = []
    p._progress = lambda stage, pct: progress.append((stage.value, pct))

    result = p.run("/tmp/anything.wav")
    assert result.detected_speakers == 2
    assert [s.label for s in result.speakers] == ["A", "B"]
    assert result.speakers[0].segment_count == 2
    assert progress[-1] == ("done", 100.0)


def test_llm_fallback_applied_when_unknown(monkeypatch):
    """When the local model returns 'unknown' and the LLM is available, the
    LLM result should replace it."""
    monkeypatch.setattr(pl.audio_utils, "to_wav_bytes", lambda *a, **k: b"wavbytes")

    class FakeLLM:
        is_available = True

        def classify(self, wav, **k):
            return GenderAgePrediction("female", "adult", "woman", 0.95, 0.95, source="llm")

    p = pl.AudioAnalysisPipeline()
    p._llm_gender_age = FakeLLM()

    unknown = GenderAgePrediction("unknown", "unknown", "0", 1.0, 1.0, source="model")
    out = p._maybe_llm_fallback(unknown, np.zeros(1600, dtype=np.float32), 16000)
    assert out.gender == "female"
    assert out.age_group == "adult"
    assert out.source == "llm"


def test_llm_fallback_skipped_when_known(monkeypatch):
    class FakeLLM:
        is_available = True

        def classify(self, wav, **k):  # pragma: no cover - must not be called
            raise AssertionError("LLM should not be called for a known prediction")

    p = pl.AudioAnalysisPipeline()
    p._llm_gender_age = FakeLLM()

    known = GenderAgePrediction("male", "adult", "man", 0.8, 0.8, source="model")
    out = p._maybe_llm_fallback(known, np.zeros(10, dtype=np.float32), 16000)
    assert out is known


def test_llm_fallback_skipped_when_unavailable():
    class FakeLLM:
        is_available = False

        def classify(self, wav, **k):  # pragma: no cover
            raise AssertionError("should not be called")

    p = pl.AudioAnalysisPipeline()
    p._llm_gender_age = FakeLLM()
    unknown = GenderAgePrediction("unknown", "unknown", None, None, None, source="model")
    assert p._maybe_llm_fallback(unknown, np.zeros(10, dtype=np.float32), 16000) is unknown
