"""Atypicality detection service.

Wraps two pre-trained artifacts that MUST be used together:

* ``atypicality_scaler.pkl``  — ``StandardScaler`` fit on 7 acoustic features.
* ``atypicality_iforest.pkl`` — ``IsolationForest`` (200 trees, contamination
  0.15) trained on the scaled features.

The scaler exposes ``feature_names_in_`` in a fixed order; the IsolationForest
does not, so feature ordering is governed entirely by the scaler. We therefore
align inputs to ``scaler.feature_names_in_`` defensively.

IsolationForest semantics:
    predict()            -> +1 inlier  (TYPICAL), -1 outlier (ATYPICAL)
    decision_function()  -> > 0 inlier, < 0 outlier; magnitude ~ confidence
"""

from __future__ import annotations

import math
import threading
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.exceptions import ModelInferenceError
from app.core.logging import get_logger
from app.models.enums import AtypicalityLabel
from app.services.ml.types import AcousticFeatures, AtypicalityPrediction

logger = get_logger(__name__)

# Canonical feature order (matches the scaler's ``feature_names_in_``).
ATYPICALITY_FEATURE_ORDER: tuple[str, ...] = (
    "latency_to_speak_sec",
    "pause_to_speech_ratio",
    "pronunciation_flux_var",
    "f0_mean",
    "jitter",
    "shimmer",
    "hnr",
)


class AtypicalityClassifier:
    """Loads the scaler + isolation forest once and classifies speakers."""

    def __init__(self, scaler_path: Path | None = None, iforest_path: Path | None = None) -> None:
        self._scaler_path = scaler_path or settings.scaler_path
        self._iforest_path = iforest_path or settings.iforest_path
        self._scaler: Any = None
        self._iforest: Any = None
        self._feature_order: tuple[str, ...] = ATYPICALITY_FEATURE_ORDER
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        """Eagerly load both artifacts (idempotent, thread-safe)."""
        if self._scaler is not None and self._iforest is not None:
            return
        with self._lock:
            if self._scaler is not None and self._iforest is not None:
                return
            import joblib

            for path in (self._scaler_path, self._iforest_path):
                if not Path(path).exists():
                    raise ModelInferenceError(
                        f"Atypicality model artifact not found: {path}",
                        code="model_missing",
                    )
            logger.info(
                "atypicality_model_load",
                scaler=str(self._scaler_path),
                iforest=str(self._iforest_path),
            )
            # The artifacts were pickled with an older scikit-learn; the
            # version-mismatch warning is expected and benign for these
            # estimators. Silence it to keep logs clean.
            import warnings

            from sklearn.exceptions import InconsistentVersionWarning

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InconsistentVersionWarning)
                self._scaler = joblib.load(self._scaler_path)
                self._iforest = joblib.load(self._iforest_path)

            names = getattr(self._scaler, "feature_names_in_", None)
            if names is not None:
                self._feature_order = tuple(str(n) for n in names)
            logger.info("atypicality_model_ready", features=list(self._feature_order))

    @property
    def is_loaded(self) -> bool:
        return self._scaler is not None and self._iforest is not None

    # --------------------------------------------------------------- predict
    def predict(self, features: AcousticFeatures) -> AtypicalityPrediction:
        """Classify a single speaker as TYPICAL / ATYPICAL."""
        self.load()
        import numpy as np

        feature_map = features.as_dict()
        try:
            row = [float(feature_map[name]) for name in self._feature_order]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ModelInferenceError(
                f"Missing acoustic feature for atypicality model: {exc}",
                code="feature_missing",
            ) from exc

        X = np.asarray([row], dtype=float)
        try:
            # Pass a named DataFrame so the scaler aligns by feature name and
            # does not emit a "missing feature names" warning. The downstream
            # IsolationForest was fit without names, so it receives the scaled
            # numpy array directly.
            import pandas as pd

            X_named = pd.DataFrame(X, columns=list(self._feature_order))
            scaled = self._scaler.transform(X_named)
            pred = int(self._iforest.predict(scaled)[0])           # +1 / -1
            score = float(self._iforest.decision_function(scaled)[0])
        except Exception as exc:  # noqa: BLE001
            raise ModelInferenceError(f"Atypicality inference failed: {exc}") from exc

        label = (
            AtypicalityLabel.TYPICAL if pred == 1 else AtypicalityLabel.ATYPICAL
        )
        # Map the signed decision score to a 0..1 confidence via a logistic
        # squash; larger |score| => more confident either way.
        confidence = 1.0 / (1.0 + math.exp(-abs(score) * 6.0))

        return AtypicalityPrediction(
            label=label.value,
            score=round(score, 6),
            confidence=round(confidence, 4),
        )

    def get_feature_contributions(
        self, features: AcousticFeatures, baseline_score: float, top_k: int = 7
    ) -> list[dict[str, Any]]:
        """Compute feature contributions for explainability.
        
        Args:
            features: Acoustic features for the speaker
            baseline_score: The atypicality score from predict()
            top_k: Number of top features to return
            
        Returns:
            List of feature contribution dicts
        """
        self.load()
        from app.services.ml.explainability import compute_feature_contributions

        return compute_feature_contributions(
            features,
            baseline_score,
            self._scaler,
            self._iforest,
            self._feature_order,
            top_k=top_k,
        )


# --------------------------------------------------------------- singleton
_instance: AtypicalityClassifier | None = None
_instance_lock = threading.Lock()


def get_atypicality_classifier() -> AtypicalityClassifier:
    """Return the process-wide singleton."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = AtypicalityClassifier()
    return _instance
