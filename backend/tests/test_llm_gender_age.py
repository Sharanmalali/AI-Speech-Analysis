"""Tests for the Gemini gender/age fallback (no network — pure logic)."""

import pytest

from app.models.enums import AgeGroup, Gender
from app.services.ml.llm_gender_age import (
    _extract_json,
    _interpret,
    get_llm_gender_age_classifier,
)

pytestmark = pytest.mark.unit


def test_extract_json_plain():
    assert _extract_json('{"gender":"male"}') == {"gender": "male"}


def test_extract_json_fenced():
    text = '```json\n{"gender": "female", "age_group": "adult"}\n```'
    assert _extract_json(text) == {"gender": "female", "age_group": "adult"}


def test_extract_json_embedded_prose():
    text = 'Here is the result: {"category": "child"} hope this helps'
    assert _extract_json(text) == {"category": "child"}


def test_extract_json_garbage_returns_none():
    assert _extract_json("not json at all") is None


def test_interpret_woman():
    pred = _interpret({"gender": "female", "age_group": "adult", "category": "woman", "confidence": 0.9})
    assert pred.gender == Gender.FEMALE.value
    assert pred.age_group == AgeGroup.ADULT.value
    assert pred.source == "llm"
    assert pred.gender_confidence == 0.9


def test_interpret_child_forces_age():
    pred = _interpret({"gender": "unknown", "age_group": "unknown", "category": "child", "confidence": 0.7})
    assert pred.age_group == AgeGroup.CHILD.value


def test_interpret_man_infers_defaults():
    pred = _interpret({"category": "man", "confidence": "bad-number"})
    assert pred.gender == Gender.MALE.value
    assert pred.age_group == AgeGroup.ADULT.value
    assert pred.gender_confidence == 0.0  # invalid confidence coerced


def test_classifier_disabled_without_key(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    clf = get_llm_gender_age_classifier()
    assert clf.is_available is False
    assert clf.classify(b"fakebytes") is None
