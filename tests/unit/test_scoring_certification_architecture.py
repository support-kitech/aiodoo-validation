"""Unit tests for score dimensions and certification criteria architecture."""

from __future__ import annotations

from aiodoo_validation.certification.criteria import (
    CertificationCriteria,
    default_structural_certification_criteria,
    evaluate_certification_criteria,
)
from aiodoo_validation.domain.enums import ExecutionTier, ScoreDimensionName
from aiodoo_validation.scoring.dimensions import (
    compute_weighted_score,
    structural_dimensions_from_oracle,
)


def test_structural_dimensions_and_weighted_helper() -> None:
    dims = structural_dimensions_from_oracle(oracle_success=True, score=100.0)
    mapping = dims.as_mapping()
    assert mapping[ScoreDimensionName.STRUCTURAL.value] == 100.0
    assert mapping[ScoreDimensionName.WEIGHTED.value] == 100.0
    weighted = compute_weighted_score(
        {"structural": 100.0, "behavior": None},
        {"structural": 1.0, "behavior": 1.0},
    )
    assert weighted == 100.0
    assert compute_weighted_score({}, {"structural": 1.0}) is None


def test_standard_tier_never_certifies() -> None:
    evaluation = evaluate_certification_criteria(
        default_structural_certification_criteria(),
        execution_tier=ExecutionTier.STANDARD,
        structural_pass=True,
        benchmark_pass=True,
        oracle_score=100.0,
        benchmark_score=100.0,
    )
    assert evaluation.eligible is False
    assert evaluation.certified is False
    assert "standard_tier_never_certifies" in evaluation.reasons


def test_smoke_certifies_when_criteria_pass() -> None:
    evaluation = evaluate_certification_criteria(
        default_structural_certification_criteria(),
        execution_tier=ExecutionTier.SMOKE,
        structural_pass=True,
        benchmark_pass=True,
        oracle_score=100.0,
        benchmark_score=100.0,
    )
    assert evaluation.eligible is True
    assert evaluation.certified is True


def test_behavior_required_criteria_denies_when_deferred() -> None:
    criteria = CertificationCriteria(
        require_structural_pass=True,
        require_behavior_pass=True,
        require_benchmark_pass=True,
    )
    evaluation = evaluate_certification_criteria(
        criteria,
        execution_tier=ExecutionTier.FULL,
        structural_pass=True,
        behavior_pass=None,
        behavior_deferred=True,
        benchmark_pass=True,
        oracle_score=100.0,
        benchmark_score=100.0,
    )
    assert evaluation.certified is False
    assert "behavior_deferred" in evaluation.reasons
