"""Gender & age-group classification service.

Wraps ``gender_age_clf.pkl`` — a ``RandomForestClassifier`` whose
``feature_names_in_`` are ``['1' .. '480', 'F0_Mean', 'Jitter', 'Shimmer']``
(483 features total).

IMPORTANT — model provenance caveat
-----------------------------------
The supplied artifact was trained on data containing a SINGLE class
(``classes_ == [0]``); it will therefore always predict ``0`` regardless of
input. We load and use it exactly as provided (no retraining). To keep the
service correct for a properly-trained replacement, we:

* read ``model.classes_`` at runtime,
* map each raw class label to a (gender, age_group) pair via a configurable
  ``label_map`` (string conventions like ``"male_adult"`` are parsed
  automatically),
* derive confidence from ``predict_proba``.

The first 480 features have no recoverable names in the pickle. We therefore
feed a deterministic, documented acoustic representation (a flattened log-mel
summary produced by :mod:`feature_extraction`) so the contract is stable and
can be aligned with the original training pipeline if/when it is shared.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.exceptions import ModelInferenceError
from app.core.logging import get_logger
from app.models.enums import AgeGroup, Gender
from app.services.ml.types import AcousticFeatures, GenderAgePrediction

logger = get_logger(__name__)

# Trailing named features in the model's expected order.
TRAILING_FEATURES: tuple[str, ...] = ("F0_Mean", "Jitter", "Shimmer")

# Default mapping from raw class label -> (gender, age_group). Extend or
# override via the constructor / settings for a multi-class replacement model.
DEFAULT_LABEL_MAP: dict[str, tuple[Gender, AgeGroup]] = {
    "male_child": (Gender.MALE, AgeGroup.CHILD),
    "male_teen": (Gender.MALE, AgeGroup.TEEN),
    "male_adult": (Gender.MALE, AgeGroup.ADULT),
    "male_senior": (Gender.MALE, AgeGroup.SENIOR),
    "female_child": (Gender.FEMALE, AgeGroup.CHILD),
    "female_teen": (Gender.FEMALE, AgeGroup.TEEN),
    "female_adult": (Gender.FEMALE, AgeGroup.ADULT),
    "female_senior": (Gender.FEMALE, AgeGroup.SENIOR),
}

_GENDER_TOKENS = {g.value: g for g in Gender}
_AGE_TOKENS = {a.value: a for a in AgeGroup}


def _parse_label(raw: str) -> tuple[Gender, AgeGroup]:
    """Best-effort parse of a raw class label into (gender, age_group)."""
    key = str(raw).strip().lower()
    if key in DEFAULT_LABEL_MAP:
        return DEFAULT_LABEL_MAP[key]

    gender = Gender.UNKNOWN
    age = AgeGroup.UNKNOWN
    tokens = key.replace("-", "_").replace(" ", "_").split("_")
    for tok in tokens:
        if tok in _GENDER_TOKENS:
            gender = _GENDER_TOKENS[tok]
        if tok in _AGE_TOKENS:
            age = _AGE_TOKENS[tok]
    return gender, age


class GenderAgeClassifier:
    """Loads the gender/age model once and predicts per-speaker."""

    def __init__(
        self,
        model_path: Path | None = None,
        label_map: dict[str, tuple[Gender, AgeGroup]] | None = None,
    ) -> None:
        self._model_path = model_path or settings.gender_age_path
        self._model: Any = None
        self._feature_names: list[str] = []
        self._n_features: int = 483
        self._classes: list[Any] = []
        self._is_degenerate: bool = False
        self._label_map = label_map or DEFAULT_LABEL_MAP
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            if not Path(self._model_path).exists():
                raise ModelInferenceError(
                    f"Gender/age model artifact not found: {self._model_path}",
                    code="model_missing",
                )
            import joblib

            logger.info("gender_age_model_load", path=str(self._model_path))
            import warnings

            from sklearn.exceptions import InconsistentVersionWarning

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InconsistentVersionWarning)
                self._model = joblib.load(self._model_path)

            self._n_features = int(getattr(self._model, "n_features_in_", 483))
            names = getattr(self._model, "feature_names_in_", None)
            self._feature_names = [str(n) for n in names] if names is not None else []
            self._classes = list(getattr(self._model, "classes_", []))
            self._is_degenerate = len(self._classes) <= 1
            if self._is_degenerate:
                logger.warning(
                    "gender_age_model_degenerate",
                    classes=self._classes,
                    note="model has <=1 class; predictions will be uninformative",
                )
            logger.info(
                "gender_age_model_ready",
                n_features=self._n_features,
                n_classes=len(self._classes),
            )

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def is_degenerate(self) -> bool:
        self.load()
        return self._is_degenerate

    # --------------------------------------------------------------- helpers
    def _build_input_row(self, features: AcousticFeatures) -> list[float]:
        """Assemble the 483-dim feature row in the model's expected order."""
        n_trailing = len(TRAILING_FEATURES)
        n_leading = max(0, self._n_features - n_trailing)

        vector = list(features.gender_age_vector or [])
        if len(vector) < n_leading:
            vector = vector + [0.0] * (n_leading - len(vector))
        else:
            vector = vector[:n_leading]

        trailing = [features.f0_mean, features.jitter, features.shimmer]
        return [float(v) for v in (*vector, *trailing[:n_trailing])]

    # --------------------------------------------------------------- predict
    def predict(self, features: AcousticFeatures) -> GenderAgePrediction:
        self.load()
        import numpy as np

        row = self._build_input_row(features)
        X = np.asarray([row], dtype=float)

        try:
            # Use a named DataFrame when the model carries feature names so
            # alignment is by name and no warning is emitted.
            if self._feature_names and len(self._feature_names) == len(row):
                import pandas as pd

                X_in: Any = pd.DataFrame(X, columns=self._feature_names)
            else:
                X_in = X
            raw_pred = self._model.predict(X_in)[0]
            confidence: float | None = None
            if hasattr(self._model, "predict_proba"):
                proba = self._model.predict_proba(X_in)[0]
                confidence = float(np.max(proba))
        except Exception as exc:  # noqa: BLE001
            raise ModelInferenceError(f"Gender/age inference failed: {exc}") from exc

        raw_label = str(raw_pred)
        gender, age = _parse_label(raw_label)

        return GenderAgePrediction(
            gender=gender.value,
            age_group=age.value,
            raw_label=raw_label,
            gender_confidence=round(confidence, 4) if confidence is not None else None,
            age_confidence=round(confidence, 4) if confidence is not None else None,
        )


# --------------------------------------------------------------- singleton
_instance: GenderAgeClassifier | None = None
_instance_lock = threading.Lock()


def get_gender_age_classifier() -> GenderAgeClassifier:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = GenderAgeClassifier()
    return _instance
