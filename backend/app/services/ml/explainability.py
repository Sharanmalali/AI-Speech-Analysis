"""Explainability service for atypicality predictions.

Computes per-feature contributions to the atypicality score, enabling
clinicians to understand which acoustic characteristics drove the model's
assessment. Uses a permutation-based importance approach that measures how
much each feature impacts the IsolationForest decision function.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.core.logging import get_logger
from app.services.ml.types import AcousticFeatures

logger = get_logger(__name__)

# Canonical feature order matching the atypicality model
ATYPICALITY_FEATURE_ORDER: tuple[str, ...] = (
    "latency_to_speak_sec",
    "pause_to_speech_ratio",
    "pronunciation_flux_var",
    "f0_mean",
    "jitter",
    "shimmer",
    "hnr",
)

# Human-readable feature names for display
FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "latency_to_speak_sec": "Latency to Speak",
    "pause_to_speech_ratio": "Pause-to-Speech Ratio",
    "pronunciation_flux_var": "Pronunciation Flux",
    "f0_mean": "F0 Mean (Pitch)",
    "jitter": "Jitter",
    "shimmer": "Shimmer",
    "hnr": "HNR (Noise)",
}


class ExplainabilityService:
    """Computes feature contributions for atypicality predictions."""

    def __init__(self, scaler: Any, iforest: Any, feature_order: tuple[str, ...]) -> None:
        """Initialize with loaded scaler and IsolationForest model.
        
        Args:
            scaler: Fitted StandardScaler
            iforest: Fitted IsolationForest model
            feature_order: Tuple of feature names in the expected order
        """
        self._scaler = scaler
        self._iforest = iforest
        self._feature_order = feature_order

    def compute_contributions(
        self,
        features: AcousticFeatures,
        baseline_score: float,
        top_k: int = 7,
    ) -> list[dict[str, Any]]:
        """Compute per-feature contributions to the atypicality score.
        
        Uses a permutation approach: for each feature, replace it with the
        feature mean (neutral value) and measure the change in decision score.
        Larger changes indicate higher feature importance.
        
        Args:
            features: Acoustic features for the speaker
            baseline_score: Original atypicality score (from decision_function)
            top_k: Return only the top K most impactful features
            
        Returns:
            List of dicts with keys: feature, display_name, contribution, value, direction
            Sorted by absolute contribution (descending)
        """
        import pandas as pd

        feature_map = features.as_dict()
        try:
            row = np.asarray(
                [[float(feature_map[name]) for name in self._feature_order]],
                dtype=float,
            )
        except KeyError as exc:
            logger.warning("explainability_feature_missing", error=str(exc))
            return []

        # Scale the original features
        X_named = pd.DataFrame(row, columns=list(self._feature_order))
        scaled = self._scaler.transform(X_named)
        
        # Compute mean of each feature in the scaled space (neutral baseline)
        # For simplicity, use 0 (mean of standard-scaled features)
        feature_means = np.zeros(scaled.shape[1])

        contributions = []
        for idx, feature_name in enumerate(self._feature_order):
            # Create a copy with this feature replaced by its mean
            perturbed = scaled.copy()
            perturbed[0, idx] = feature_means[idx]
            
            # Compute new score
            perturbed_score = float(self._iforest.decision_function(perturbed)[0])
            
            # Contribution = how much the score changed when we neutralized this feature
            # Positive contribution = feature pushed towards ATYPICAL (negative score)
            # Negative contribution = feature pushed towards TYPICAL (positive score)
            contribution = baseline_score - perturbed_score
            
            # Direction: "high" if feature value is above mean (in scaled space)
            # "low" if below mean, "normal" if near mean
            scaled_value = scaled[0, idx]
            if abs(scaled_value) < 0.5:
                direction = "normal"
            elif scaled_value > 0:
                direction = "high"
            else:
                direction = "low"
            
            contributions.append({
                "feature": feature_name,
                "display_name": FEATURE_DISPLAY_NAMES.get(feature_name, feature_name),
                "contribution": round(float(contribution), 4),
                "value": round(float(feature_map[feature_name]), 4),
                "scaled_value": round(float(scaled_value), 4),
                "direction": direction,
            })
        
        # Sort by absolute contribution (descending) and take top K
        contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        top_contributions = contributions[:top_k]
        
        logger.info(
            "explainability_computed",
            baseline_score=round(baseline_score, 4),
            top_features=[c["feature"] for c in top_contributions],
        )
        
        return top_contributions


def compute_feature_contributions(
    features: AcousticFeatures,
    baseline_score: float,
    scaler: Any,
    iforest: Any,
    feature_order: tuple[str, ...],
    top_k: int = 7,
) -> list[dict[str, Any]]:
    """Convenience function to compute feature contributions.
    
    Args:
        features: Acoustic features for the speaker
        baseline_score: Original atypicality score
        scaler: Fitted StandardScaler
        iforest: Fitted IsolationForest
        feature_order: Feature names in expected order
        top_k: Number of top features to return
        
    Returns:
        List of feature contribution dicts
    """
    service = ExplainabilityService(scaler, iforest, feature_order)
    return service.compute_contributions(features, baseline_score, top_k=top_k)
