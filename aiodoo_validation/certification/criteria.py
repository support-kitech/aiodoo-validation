"""Reusable certification criteria architecture.

Production policies still certify from benchmark pass today. Criteria objects
document the dimensions that future profile thresholds will evaluate without
hardcoding profile-specific strings in the engine.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ExecutionTier, ValidationKind
from aiodoo_validation.execution import allows_certification


@dataclass(frozen=True, slots=True)
class CertificationCriteria:
    """
    Declared certification inputs for a policy.

    All fields are optional so policies can start with benchmark-only checks
    and grow to structural + behavioral + score thresholds without redesign.
    """

    require_structural_pass: bool = True
    require_behavior_pass: bool = False
    require_benchmark_pass: bool = True
    min_oracle_score: float | None = 100.0
    min_behavior_score: float | None = None
    min_weighted_score: float | None = None
    min_benchmark_score: float | None = 100.0
    profile_thresholds: Mapping[str, float] = field(
        default_factory=lambda: MappingProxyType({})
    )
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class CriteriaEvaluation:
    """Result of evaluating CertificationCriteria against observed signals."""

    eligible: bool
    certified: bool
    reasons: tuple[str, ...]
    signals: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


def evaluate_certification_criteria(
    criteria: CertificationCriteria,
    *,
    execution_tier: ExecutionTier | str,
    structural_pass: bool | None = None,
    behavior_pass: bool | None = None,
    behavior_deferred: bool = False,
    benchmark_pass: bool | None = None,
    oracle_score: float | None = None,
    behavior_score: float | None = None,
    weighted_score: float | None = None,
    benchmark_score: float | None = None,
    validation_kind: ValidationKind | None = None,
) -> CriteriaEvaluation:
    """
    Evaluate reusable certification criteria.

    Never fabricates missing signals into passes. Missing required signals
    produce denial reasons. Standard tier is never eligible.
    """
    reasons: list[str] = []
    signals: dict[str, Any] = {
        "structural_pass": structural_pass,
        "behavior_pass": behavior_pass,
        "behavior_deferred": behavior_deferred,
        "benchmark_pass": benchmark_pass,
        "oracle_score": oracle_score,
        "behavior_score": behavior_score,
        "weighted_score": weighted_score,
        "benchmark_score": benchmark_score,
        "validation_kind": validation_kind.value if validation_kind else None,
        "execution_tier": getattr(execution_tier, "value", str(execution_tier)),
    }

    if not allows_certification(execution_tier):
        return CriteriaEvaluation(
            eligible=False,
            certified=False,
            reasons=("standard_tier_never_certifies",),
            signals=MappingProxyType(signals),
        )

    if criteria.require_benchmark_pass:
        if benchmark_pass is None:
            reasons.append("benchmark_pass_missing")
        elif not benchmark_pass:
            reasons.append("benchmark_failed")

    if criteria.require_structural_pass and structural_pass is False:
        reasons.append("structural_failed")

    if criteria.require_behavior_pass:
        if behavior_deferred or behavior_pass is None:
            reasons.append("behavior_not_available")
        elif not behavior_pass:
            reasons.append("behavior_failed")

    if criteria.min_oracle_score is not None and oracle_score is not None:
        if oracle_score < criteria.min_oracle_score:
            reasons.append("oracle_score_below_threshold")

    if criteria.min_behavior_score is not None:
        if behavior_score is None:
            reasons.append("behavior_score_missing")
        elif behavior_score < criteria.min_behavior_score:
            reasons.append("behavior_score_below_threshold")

    if criteria.min_weighted_score is not None:
        if weighted_score is None:
            reasons.append("weighted_score_missing")
        elif weighted_score < criteria.min_weighted_score:
            reasons.append("weighted_score_below_threshold")

    if criteria.min_benchmark_score is not None and benchmark_score is not None:
        if benchmark_score < criteria.min_benchmark_score:
            reasons.append("benchmark_score_below_threshold")

    for key, threshold in criteria.profile_thresholds.items():
        observed = signals.get(key)
        if observed is None:
            reasons.append(f"profile_threshold_missing:{key}")
        elif float(observed) < float(threshold):
            reasons.append(f"profile_threshold_failed:{key}")

    certified = not reasons
    return CriteriaEvaluation(
        eligible=True,
        certified=certified,
        reasons=tuple(reasons) if reasons else ("criteria_satisfied",),
        signals=MappingProxyType(signals),
    )


def default_structural_certification_criteria() -> CertificationCriteria:
    """Current production criteria: structural/benchmark path (no behavior yet)."""
    return CertificationCriteria(
        require_structural_pass=True,
        require_behavior_pass=False,
        require_benchmark_pass=True,
        min_oracle_score=100.0,
        min_benchmark_score=100.0,
        metadata=MappingProxyType({"mode": "structural_v1"}),
    )


__all__ = [
    "CertificationCriteria",
    "CriteriaEvaluation",
    "default_structural_certification_criteria",
    "evaluate_certification_criteria",
]
