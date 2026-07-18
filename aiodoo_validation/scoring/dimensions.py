"""Multi-dimensional score architecture.

Production policies may still emit a single primary ``score`` (often 100/0).
``ScoreDimensions`` records the architectural breakdown for reporting and
future weighted certification without inventing values.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ScoreDimensionName, ValidationKind


@dataclass(frozen=True, slots=True)
class ScoreDimensions:
    """Optional score dimensions attached to a ScoreResult via metadata."""

    oracle: float | None = None
    behavior: float | None = None
    syntax: float | None = None
    structural: float | None = None
    policy: float | None = None
    weighted: float | None = None
    validation_kind: ValidationKind = ValidationKind.STRUCTURAL
    weights: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    extras: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def as_mapping(self) -> Mapping[str, Any]:
        payload: dict[str, Any] = {
            "validation_kind": self.validation_kind.value,
            ScoreDimensionName.ORACLE.value: self.oracle,
            ScoreDimensionName.BEHAVIOR.value: self.behavior,
            ScoreDimensionName.SYNTAX.value: self.syntax,
            ScoreDimensionName.STRUCTURAL.value: self.structural,
            ScoreDimensionName.POLICY.value: self.policy,
            ScoreDimensionName.WEIGHTED.value: self.weighted,
        }
        if self.weights:
            payload["weights"] = dict(self.weights)
        if self.extras:
            payload["extras"] = dict(self.extras)
        return MappingProxyType(payload)


def compute_weighted_score(
    dimensions: Mapping[str, float | None],
    weights: Mapping[str, float],
) -> float | None:
    """
    Compute a weighted aggregate from available dimensions.

    Dimensions with ``None`` values are skipped. Returns ``None`` when no
    weighted terms are available (never fabricates a score).
    """
    total_weight = 0.0
    accumulator = 0.0
    for name, weight in weights.items():
        if weight <= 0:
            continue
        value = dimensions.get(name)
        if value is None:
            continue
        accumulator += float(value) * float(weight)
        total_weight += float(weight)
    if total_weight <= 0:
        return None
    return accumulator / total_weight


def structural_dimensions_from_oracle(*, oracle_success: bool, score: float) -> ScoreDimensions:
    """Build structural score dimensions from an oracle outcome."""
    structural = score if oracle_success else 0.0
    return ScoreDimensions(
        oracle=score,
        structural=structural,
        behavior=None,
        syntax=None,
        policy=None,
        weighted=structural,
        validation_kind=ValidationKind.STRUCTURAL,
        weights=MappingProxyType({ScoreDimensionName.STRUCTURAL.value: 1.0}),
    )


def behavior_dimensions_from_suite(
    *,
    pass_rate: float | None,
    oracle_score: float | None = None,
) -> ScoreDimensions:
    """Build behavioral score dimensions from a suite pass rate (0–100)."""
    return ScoreDimensions(
        oracle=oracle_score,
        behavior=pass_rate,
        structural=None,
        syntax=None,
        policy=None,
        weighted=pass_rate,
        validation_kind=ValidationKind.BEHAVIORAL,
        weights=MappingProxyType({ScoreDimensionName.BEHAVIOR.value: 1.0}),
    )


__all__ = [
    "ScoreDimensions",
    "behavior_dimensions_from_suite",
    "compute_weighted_score",
    "structural_dimensions_from_oracle",
]
