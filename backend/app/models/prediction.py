"""Prediction ORM model — per-speaker model outputs."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AgeGroup, AtypicalityLabel, Gender

# Use JSONB on Postgres, fall back to generic JSON elsewhere (e.g. SQLite dev).
JSONType = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from app.models.speaker import Speaker


class Prediction(Base, UUIDMixin, TimestampMixin):
    """Aggregated model predictions for a single speaker."""

    __tablename__ = "predictions"

    speaker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("speakers.id", ondelete="CASCADE"), index=True, nullable=False, unique=True
    )

    # --- Gender ---
    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, name="gender", native_enum=False, length=16),
        default=Gender.UNKNOWN,
        nullable=False,
    )
    gender_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Age group ---
    age_group: Mapped[AgeGroup] = mapped_column(
        Enum(AgeGroup, name="age_group", native_enum=False, length=16),
        default=AgeGroup.UNKNOWN,
        nullable=False,
    )
    age_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raw label emitted by the (combined gender/age) classifier.
    raw_class_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # --- Atypicality ---
    atypicality: Mapped[AtypicalityLabel] = mapped_column(
        Enum(AtypicalityLabel, name="atypicality", native_enum=False, length=16),
        default=AtypicalityLabel.UNKNOWN,
        nullable=False,
    )
    atypicality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    atypicality_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # The acoustic features that fed the models (for transparency/audit).
    features: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    # --- Relationships -------------------------------------------------------
    speaker: Mapped["Speaker"] = relationship(back_populates="prediction")

    @property
    def gender_age_source(self) -> str:
        """Provenance of the gender/age prediction: 'model' or 'llm'.

        Stored inside the ``features`` JSON to avoid a dedicated column.
        """
        if isinstance(self.features, dict):
            return str(self.features.get("gender_age_source") or "model")
        return "model"

    @property
    def feature_contributions(self) -> list[dict] | None:
        """Feature contributions for explainability.

        Stored inside the ``features`` JSON alongside acoustic features.
        """
        if isinstance(self.features, dict):
            return self.features.get("feature_contributions")
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Prediction gender={self.gender.value} age={self.age_group.value} "
            f"atypicality={self.atypicality.value}>"
        )
