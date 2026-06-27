"""ML service tests exercising the real model artifacts."""

import pytest

from app.models.enums import AgeGroup, Gender
from app.services.ml.atypicality_classifier import (
    ATYPICALITY_FEATURE_ORDER,
    get_atypicality_classifier,
)
from app.services.ml.gender_age_classifier import _parse_label, get_gender_age_classifier
from app.services.ml.types import AcousticFeatures

pytestmark = pytest.mark.ml


def _features(**overrides) -> AcousticFeatures:
    base = dict(
        latency_to_speak_sec=1.0,
        pause_to_speech_ratio=0.5,
        pronunciation_flux_var=4.0,
        f0_mean=200.0,
        jitter=0.02,
        shimmer=0.1,
        hnr=13.0,
        gender_age_vector=[0.1] * 480,
    )
    base.update(overrides)
    return AcousticFeatures(**base)


def test_atypicality_feature_order():
    assert ATYPICALITY_FEATURE_ORDER == (
        "latency_to_speak_sec",
        "pause_to_speech_ratio",
        "pronunciation_flux_var",
        "f0_mean",
        "jitter",
        "shimmer",
        "hnr",
    )


def test_atypicality_typical_vs_outlier():
    clf = get_atypicality_classifier()
    clf.load()
    # The scaler mean should be classified as a clear inlier (typical).
    mean_feats = AcousticFeatures(*[float(x) for x in clf._scaler.mean_])
    typ = clf.predict(mean_feats)
    assert typ.label in {"typical", "atypical"}
    assert 0.0 <= typ.confidence <= 1.0

    outlier = _features(
        latency_to_speak_sec=50, pause_to_speech_ratio=5, pronunciation_flux_var=99,
        f0_mean=600, jitter=0.5, shimmer=0.9, hnr=-5,
    )
    out = clf.predict(outlier)
    # The extreme point should score lower than the distribution mean.
    assert out.score <= typ.score


def test_gender_age_loads_483_features():
    clf = get_gender_age_classifier()
    clf.load()
    assert clf._n_features == 483
    row = clf._build_input_row(_features())
    assert len(row) == 483
    pred = clf.predict(_features())
    assert pred.raw_label is not None


def test_parse_label_mapping():
    assert _parse_label("male_adult") == (Gender.MALE, AgeGroup.ADULT)
    assert _parse_label("female_child") == (Gender.FEMALE, AgeGroup.CHILD)
    assert _parse_label("FEMALE-SENIOR") == (Gender.FEMALE, AgeGroup.SENIOR)
    assert _parse_label("0") == (Gender.UNKNOWN, AgeGroup.UNKNOWN)
