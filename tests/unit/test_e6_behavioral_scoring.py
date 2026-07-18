"""E6 behavioral scoring integration tests."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from aiodoo_validation.domain.enums import ExecutionTier, ValidationKind
from aiodoo_validation.domain.oracle import OracleExecutionResult, OracleResult
from aiodoo_validation.domain.scoring import ScoreContext
from aiodoo_validation.profiles.adapter_profile import AdapterProfile
from aiodoo_validation.scoring.behavioral import (
    SCORING_POLICY_REF_KEY,
    BehavioralEvidenceScorePolicy,
)
from aiodoo_validation.scoring.dimensions import (
    behavior_dimensions_from_evidence,
    compute_weighted_score,
)
from aiodoo_validation.scoring.evidence import (
    DIM_BEHAVIOR,
    DIM_TRANSFORM_CORRECTNESS,
    interpret_behavioral_oracle_evidence,
)
from aiodoo_validation.scoring.ids import CODING_SCORE_BEHAVIOR, REPAIR_SCORE_BEHAVIOR
from aiodoo_validation.scoring.policy_defaults import (
    DEFAULT_BEHAVIORAL_POLICY_REF,
    BehavioralScoringPolicyData,
)
from aiodoo_validation.scoring.policy_loader import (
    ScoringPolicyLoadError,
    load_behavioral_scoring_policy,
)
from aiodoo_validation.scoring.production import default_production_score_policies


def _oracle(
    *,
    success: bool = True,
    deferred: bool = False,
    transforms_passed: bool | None = None,
    case_count: int | None = None,
    pass_count: int | None = None,
    fail_count: int | None = None,
    findings: tuple[str, ...] = (),
    extra_meta: dict | None = None,
) -> OracleResult:
    meta: dict = {
        "deferred": deferred,
        "validation_kind": ValidationKind.BEHAVIORAL.value,
        "capability_id": "repair",
    }
    if transforms_passed is not None:
        meta["transforms_passed"] = transforms_passed
        meta["transform_case_count"] = 1
    if case_count is not None:
        meta["case_count"] = case_count
    if pass_count is not None:
        meta["pass_count"] = pass_count
    if fail_count is not None:
        meta["fail_count"] = fail_count
    if extra_meta:
        meta.update(extra_meta)
    return OracleResult(
        oracle_id="repair.oracle.behavior.repair",
        success=success,
        message="test",
        findings=findings,
        duration_ms=1,
        metadata=MappingProxyType(meta),
    )


def _context(oracle: OracleResult, *, configuration: dict | None = None) -> ScoreContext:
    execution = OracleExecutionResult(
        plan_digest="digest",
        profile_name="repair",
        results=(oracle,),
        duration_ms=1,
        oracle_count=1,
        success_count=1 if oracle.success else 0,
        failure_count=0 if oracle.success else 1,
    )
    return ScoreContext(
        run_id="run-1",
        profile_name="repair",
        plan_digest="digest",
        protocol_major=1,
        protocol_minor=0,
        execution_tier=ExecutionTier.SMOKE,
        oracle_result=oracle,
        oracle_execution=execution,
        configuration=MappingProxyType(configuration or {}),
    )


def test_policy_loader_default_and_missing() -> None:
    policy = load_behavioral_scoring_policy(DEFAULT_BEHAVIORAL_POLICY_REF)
    assert policy.policy_ref == DEFAULT_BEHAVIORAL_POLICY_REF
    assert DIM_TRANSFORM_CORRECTNESS in policy.weights
    assert policy.missing_evidence == "skip"
    with pytest.raises(ScoringPolicyLoadError):
        load_behavioral_scoring_policy("missing_policy.yaml")


def test_evidence_transform_success_behavior_success() -> None:
    oracle = _oracle(
        transforms_passed=True,
        case_count=4,
        pass_count=4,
        fail_count=0,
        findings=("transform:pass", "c1:pass", "c2:pass", "c3:pass", "c4:pass"),
    )
    evidence = interpret_behavioral_oracle_evidence(oracle)
    assert evidence.transform_correctness == 100.0
    assert evidence.behavior == 100.0
    assert evidence.pass_rate == 100.0
    assert evidence.syntax is None
    assert evidence.minimal_change is None
    assert evidence.hallucination is None


def test_evidence_transform_failure_behavior_failure() -> None:
    oracle = _oracle(
        success=False,
        transforms_passed=False,
        case_count=2,
        pass_count=0,
        fail_count=2,
        findings=("transform:fail", "c1:fail", "c2:fail"),
    )
    evidence = interpret_behavioral_oracle_evidence(oracle)
    assert evidence.transform_correctness == 0.0
    assert evidence.behavior == 0.0


def test_evidence_mixed_transform_pass_behavior_partial() -> None:
    oracle = _oracle(
        success=False,
        transforms_passed=True,
        case_count=4,
        pass_count=2,
        fail_count=2,
        findings=("transform:pass", "c1:pass", "c2:fail"),
    )
    evidence = interpret_behavioral_oracle_evidence(oracle)
    assert evidence.transform_correctness == 100.0
    assert evidence.behavior == 50.0


def test_evidence_missing_and_deferred() -> None:
    deferred = _oracle(deferred=True, findings=("behavioral_deferred",))
    evidence = interpret_behavioral_oracle_evidence(deferred)
    assert evidence.deferred is True
    assert evidence.transform_correctness is None
    assert evidence.behavior is None
    assert evidence.pass_rate is None


def test_evidence_deferred_with_transform_only() -> None:
    oracle = _oracle(
        deferred=True,
        transforms_passed=True,
        findings=("behavioral_deferred", "transform:pass"),
    )
    evidence = interpret_behavioral_oracle_evidence(oracle)
    assert evidence.transform_correctness == 100.0
    assert evidence.behavior is None


def test_hallucination_from_explicit_finding_only() -> None:
    with_marker = _oracle(
        transforms_passed=False,
        findings=("transform:fail", "search_not_found:models.py"),
    )
    assert interpret_behavioral_oracle_evidence(with_marker).hallucination == 0.0
    without = _oracle(transforms_passed=False, findings=("transform:fail",))
    assert interpret_behavioral_oracle_evidence(without).hallucination is None


def test_dimension_aggregation_skips_missing() -> None:
    oracle = _oracle(
        transforms_passed=True,
        case_count=2,
        pass_count=1,
        fail_count=1,
    )
    evidence = interpret_behavioral_oracle_evidence(oracle)
    policy = load_behavioral_scoring_policy()
    dims = behavior_dimensions_from_evidence(evidence=evidence, policy=policy)
    assert dims.extras[DIM_TRANSFORM_CORRECTNESS] == 100.0
    assert dims.behavior == 50.0
    assert dims.syntax is None
    expected = compute_weighted_score(
        {
            DIM_TRANSFORM_CORRECTNESS: 100.0,
            DIM_BEHAVIOR: 50.0,
        },
        {
            DIM_TRANSFORM_CORRECTNESS: policy.weights[DIM_TRANSFORM_CORRECTNESS],
            DIM_BEHAVIOR: policy.weights[DIM_BEHAVIOR],
        },
    )
    # Renormalize against full policy weights that have evidence only.
    assert dims.weighted == pytest.approx(
        (100.0 * policy.weights[DIM_TRANSFORM_CORRECTNESS] + 50.0 * policy.weights[DIM_BEHAVIOR])
        / (policy.weights[DIM_TRANSFORM_CORRECTNESS] + policy.weights[DIM_BEHAVIOR])
    )
    assert expected == pytest.approx(dims.weighted)


def test_dimension_aggregation_zero_missing_mode() -> None:
    evidence = interpret_behavioral_oracle_evidence(
        _oracle(transforms_passed=True, case_count=1, pass_count=1, fail_count=0)
    )
    base = load_behavioral_scoring_policy()
    zero_policy = BehavioralScoringPolicyData(
        policy_ref="zero-test",
        weights=base.weights,
        binary_dimensions=base.binary_dimensions,
        missing_evidence="zero",
    )
    dims = behavior_dimensions_from_evidence(evidence=evidence, policy=zero_policy)
    assert dims.syntax == 0.0
    assert dims.weighted is not None
    assert dims.weighted < 100.0


def test_behavioral_policy_transform_and_behavior_success() -> None:
    policy = BehavioralEvidenceScorePolicy.create_for_repair()
    result = policy.score(
        _context(
            _oracle(
                transforms_passed=True,
                case_count=2,
                pass_count=2,
                fail_count=0,
                findings=("transform:pass", "a:pass", "b:pass"),
            )
        )
    )
    assert result.success is True
    assert result.policy_id == REPAIR_SCORE_BEHAVIOR
    assert result.score == pytest.approx(100.0)
    assert result.metadata["deferred"] is False
    assert result.metadata["dimensions"]["extras"][DIM_TRANSFORM_CORRECTNESS] == 100.0
    assert result.metadata["dimensions"]["behavior"] == 100.0


def test_behavioral_policy_transform_fail() -> None:
    policy = BehavioralEvidenceScorePolicy.create_for_repair()
    result = policy.score(
        _context(
            _oracle(
                success=False,
                transforms_passed=False,
                case_count=1,
                pass_count=1,
                fail_count=0,
                findings=("transform:fail", "a:pass"),
            )
        )
    )
    assert result.success is True
    assert result.score < 100.0
    assert result.metadata["dimensions"]["extras"][DIM_TRANSFORM_CORRECTNESS] == 0.0
    assert result.metadata["dimensions"]["behavior"] == 100.0


def test_behavioral_policy_behavior_fail() -> None:
    policy = BehavioralEvidenceScorePolicy.create_for_repair()
    result = policy.score(
        _context(
            _oracle(
                success=False,
                transforms_passed=True,
                case_count=2,
                pass_count=0,
                fail_count=2,
                findings=("transform:pass", "a:fail", "b:fail"),
            )
        )
    )
    assert result.metadata["dimensions"]["behavior"] == 0.0
    assert result.metadata["dimensions"]["extras"][DIM_TRANSFORM_CORRECTNESS] == 100.0
    assert result.score < 100.0


def test_behavioral_policy_mixed_evidence() -> None:
    policy = BehavioralEvidenceScorePolicy.create_for_repair()
    result = policy.score(
        _context(
            _oracle(
                success=False,
                transforms_passed=True,
                case_count=4,
                pass_count=1,
                fail_count=3,
            )
        )
    )
    dims = result.metadata["dimensions"]
    assert dims["extras"][DIM_TRANSFORM_CORRECTNESS] == 100.0
    assert dims["behavior"] == 25.0
    assert dims["weighted"] == pytest.approx(result.score)


def test_behavioral_policy_missing_evidence_scores_zero() -> None:
    policy = BehavioralEvidenceScorePolicy.create_for_repair()
    result = policy.score(_context(_oracle(deferred=True, findings=("behavioral_deferred",))))
    assert result.success is True
    assert result.score == 0.0
    assert result.metadata["deferred"] is True
    assert result.metadata["dimensions"]["weighted"] is None
    assert result.metadata["dimensions"]["behavior"] is None


def test_behavioral_policy_partial_deferred_scores_transform() -> None:
    policy = BehavioralEvidenceScorePolicy.create_for_repair()
    result = policy.score(
        _context(
            _oracle(
                deferred=True,
                transforms_passed=True,
                findings=("behavioral_deferred",),
            )
        )
    )
    assert result.score == 100.0
    assert result.metadata["deferred"] is True
    assert result.metadata["dimensions"]["extras"][DIM_TRANSFORM_CORRECTNESS] == 100.0
    assert result.metadata["dimensions"]["behavior"] is None


def test_behavioral_policy_missing_policy_ref() -> None:
    policy = BehavioralEvidenceScorePolicy.create_for_repair()
    result = policy.score(
        _context(
            _oracle(transforms_passed=True, case_count=1, pass_count=1, fail_count=0),
            configuration={SCORING_POLICY_REF_KEY: "does_not_exist.yaml"},
        )
    )
    assert result.success is False
    assert result.score == 0.0
    assert result.errors
    assert result.metadata["policy_load_error"] is True


def test_default_production_policies_include_behavior_profiles() -> None:
    from aiodoo_validation.scoring.ids import PLANNER_SCORE_BEHAVIOR

    coding = default_production_score_policies(profile="coding")
    repair = default_production_score_policies(profile="repair")
    planner = default_production_score_policies(profile="planner")
    assert any(p.metadata.policy_id == CODING_SCORE_BEHAVIOR for p in coding)
    assert any(p.metadata.policy_id == REPAIR_SCORE_BEHAVIOR for p in repair)
    assert any(p.metadata.policy_id == PLANNER_SCORE_BEHAVIOR for p in planner)
    assert all(p.metadata.policy_id != REPAIR_SCORE_BEHAVIOR for p in coding)
    assert all(p.metadata.policy_id != CODING_SCORE_BEHAVIOR for p in repair)


def test_repair_profile_scoring_pipeline_includes_behavior_stage() -> None:
    profile = AdapterProfile.create("repair", odoo_versions=(18,))
    stage_ids = {stage.stage_id for stage in profile.scoring_pipeline}
    assert REPAIR_SCORE_BEHAVIOR in stage_ids


def test_coding_profile_scoring_pipeline_includes_behavior_stage() -> None:
    from aiodoo_validation.profiles.coding.profile import CodingProfile

    profile = CodingProfile.create(odoo_versions=(18,))
    coding_ids = {stage.stage_id for stage in profile.scoring_pipeline}
    assert CODING_SCORE_BEHAVIOR in coding_ids
    assert REPAIR_SCORE_BEHAVIOR not in coding_ids


def test_planner_profile_scoring_pipeline_includes_behavior_stage() -> None:
    from aiodoo_validation.scoring.ids import PLANNER_SCORE_BEHAVIOR

    profile = AdapterProfile.create("planner", odoo_versions=(18,))
    stage_ids = {stage.stage_id for stage in profile.scoring_pipeline}
    assert PLANNER_SCORE_BEHAVIOR in stage_ids


def test_pass_rate_derived_from_counts_without_pass_rate_key() -> None:
    oracle = _oracle(case_count=5, pass_count=4, fail_count=1, transforms_passed=True)
    assert "pass_rate" not in oracle.metadata
    evidence = interpret_behavioral_oracle_evidence(oracle)
    assert evidence.pass_rate == pytest.approx(80.0)
