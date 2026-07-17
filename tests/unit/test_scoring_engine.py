"""Unit tests for Phase 6 Scoring Engine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ExecutionTier,
    ExitStatus,
    ScoreErrorCode,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.scoring import ScoreCapability, ScoreError, ScoreMetadata
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.oracles import OracleEngine
from aiodoo_validation.oracles.ids import CODING_ORACLE_IDS_ENABLED, CODING_ORACLE_METADATA
from aiodoo_validation.profiles.engine import ProfileEngine
from aiodoo_validation.resolution.stub_resolver import StubArtifactResolver
from aiodoo_validation.scoring import (
    MetadataScorePolicy,
    ScoringEngine,
    ScoringRegistry,
)
from aiodoo_validation.scoring.ids import (
    CODING_SCORE_IDS_ENABLED,
    CODING_SCORE_METADATA,
    CODING_SCORE_TO_ORACLE,
    PLACEHOLDER_SCORE_VALUE,
)
from aiodoo_validation.scoring.policies import default_coding_placeholder_policies
from aiodoo_validation.validation_plan import (
    PipelineStagePlaceholder,
    ProfileCapabilities,
    ValidationPlan,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def _request() -> ValidationRequest:
    return ValidationRequest(
        profile_name="coding",
        base_model_ref=str(FIXTURES / "base_model"),
        adapter_ref=str(FIXTURES / "coding_adapter"),
        execution_tier=ExecutionTier.STANDARD,
        run_id="scoring-test",
    )


def _context_ready_for_scoring() -> RunContext:
    request = _request()
    context = RunContext.begin(request)
    artifact = StubArtifactResolver().resolve(context)
    assert artifact.success and artifact.bundle is not None
    with_bundle = context.with_artifact_bundle(artifact.bundle)
    profile_outcome = ProfileEngine.create_default().resolve_profile(with_bundle)
    assert profile_outcome.success
    assert profile_outcome.profile is not None
    assert profile_outcome.plan is not None
    with_profile = with_bundle.with_validation_profile(
        profile_outcome.profile
    ).with_validation_plan(profile_outcome.plan)
    oracle_outcome = OracleEngine.create_default().execute_oracles(with_profile)
    assert oracle_outcome.success and oracle_outcome.execution is not None
    return with_profile.with_oracle_execution(oracle_outcome.execution)


def test_score_ids_map_to_oracle_ids() -> None:
    for policy_id in CODING_SCORE_IDS_ENABLED:
        oracle_id = CODING_SCORE_TO_ORACLE[policy_id]
        assert oracle_id in CODING_ORACLE_IDS_ENABLED
        assert policy_id.replace(".score.", ".oracle.") == oracle_id


def test_scoring_registry_registers_and_resolves() -> None:
    registry = ScoringRegistry()
    policy = MetadataScorePolicy.create()
    registry.register(policy)
    assert registry.contains(CODING_SCORE_METADATA)
    assert registry.get(CODING_SCORE_METADATA) is policy


def test_scoring_registry_duplicate_fails() -> None:
    registry = ScoringRegistry()
    registry.register(MetadataScorePolicy.create())
    with pytest.raises(ScoreError) as exc_info:
        registry.register(MetadataScorePolicy.create())
    assert exc_info.value.code is ScoreErrorCode.REGISTRATION_FAILURE


def test_scoring_registry_missing_policy() -> None:
    registry = ScoringRegistry.create_default()
    with pytest.raises(ScoreError) as exc_info:
        registry.get("coding.score.unknown")
    assert exc_info.value.code is ScoreErrorCode.POLICY_NOT_FOUND


def test_default_registry_contains_placeholder_policies() -> None:
    registry = ScoringRegistry.create_default()
    expected = {policy.metadata.policy_id for policy in default_coding_placeholder_policies()}
    assert set(registry.registered_ids()) == expected


def test_placeholder_policy_returns_deterministic_score() -> None:
    context = _context_ready_for_scoring()
    assert context.oracle_execution is not None
    oracle_result = next(
        result
        for result in context.oracle_execution.results
        if result.oracle_id == CODING_ORACLE_METADATA
    )
    from aiodoo_validation.domain.scoring import ScoreContext

    plan = context.validation_plan
    assert plan is not None
    score_context = ScoreContext(
        run_id=context.run_id,
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        protocol_major=context.protocol_major,
        protocol_minor=context.protocol_minor,
        execution_tier=context.execution_tier,
        oracle_result=oracle_result,
        oracle_execution=context.oracle_execution,
        configuration=plan.configuration,
    )
    result = MetadataScorePolicy.create().score(score_context)
    assert result.success is True
    assert result.score == PLACEHOLDER_SCORE_VALUE
    assert result.source_oracle_id == CODING_ORACLE_METADATA


def test_scoring_pipeline_executes_enabled_policies() -> None:
    context = _context_ready_for_scoring()
    outcome = ScoringEngine.create_default().score(context)
    assert outcome.success is True
    assert outcome.execution is not None
    assert outcome.execution.policy_count == 6
    assert outcome.execution.success_count == 6
    assert outcome.execution.aggregate_score == PLACEHOLDER_SCORE_VALUE
    ids = tuple(result.policy_id for result in outcome.execution.results)
    assert ids == CODING_SCORE_IDS_ENABLED


def test_disabled_quality_score_policy_is_skipped() -> None:
    context = _context_ready_for_scoring()
    plan = context.validation_plan
    assert plan is not None
    quality = next(stage for stage in plan.scoring_pipeline if stage.stage_id.endswith("quality"))
    assert quality.enabled is False
    outcome = ScoringEngine.create_default().score(context)
    assert outcome.execution is not None
    assert "coding.score.quality" not in {
        result.policy_id for result in outcome.execution.results
    }


def test_missing_oracle_results_fails_gracefully() -> None:
    request = _request()
    context = RunContext.begin(request)
    artifact = StubArtifactResolver().resolve(context)
    assert artifact.bundle is not None
    with_bundle = context.with_artifact_bundle(artifact.bundle)
    profile_outcome = ProfileEngine.create_default().resolve_profile(with_bundle)
    assert profile_outcome.plan is not None and profile_outcome.profile is not None
    ready = with_bundle.with_validation_profile(profile_outcome.profile).with_validation_plan(
        profile_outcome.plan
    )
    outcome = ScoringEngine.create_default().score(ready)
    assert outcome.success is False
    assert outcome.errors[0].code is ScoreErrorCode.MISSING_ORACLE_RESULTS


def test_capability_mismatch_fails() -> None:
    context = _context_ready_for_scoring()
    plan = context.validation_plan
    assert plan is not None
    disabled = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=ProfileCapabilities(
            supports_inference=True,
            supports_oracles=True,
            supports_scoring=False,
        ),
        supported_artifact_types=plan.supported_artifact_types,
        supported_runtimes=plan.supported_runtimes,
        oracle_pipeline=plan.oracle_pipeline,
        scoring_pipeline=plan.scoring_pipeline,
        benchmark_pipeline=plan.benchmark_pipeline,
        certification_pipeline=plan.certification_pipeline,
        report_pipeline=plan.report_pipeline,
        execution_order=plan.execution_order,
        validation_stages=plan.validation_stages,
        configuration=plan.configuration,
    )
    outcome = ScoringEngine.create_default().score(context.with_validation_plan(disabled))
    assert outcome.success is False
    assert outcome.errors[0].code is ScoreErrorCode.CAPABILITY_MISMATCH


def test_unknown_policy_in_pipeline_fails() -> None:
    context = _context_ready_for_scoring()
    plan = context.validation_plan
    assert plan is not None
    broken = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=plan.capabilities,
        supported_artifact_types=plan.supported_artifact_types,
        supported_runtimes=plan.supported_runtimes,
        oracle_pipeline=plan.oracle_pipeline,
        scoring_pipeline=(
            PipelineStagePlaceholder(
                stage_id="coding.score.missing",
                name="Missing",
                enabled=True,
                phase="scoring",
            ),
        ),
        benchmark_pipeline=plan.benchmark_pipeline,
        certification_pipeline=plan.certification_pipeline,
        report_pipeline=plan.report_pipeline,
        execution_order=plan.execution_order,
        validation_stages=plan.validation_stages,
        configuration=plan.configuration,
    )
    outcome = ScoringEngine.create_default().score(context.with_validation_plan(broken))
    assert outcome.success is False
    assert outcome.errors[0].code is ScoreErrorCode.POLICY_NOT_FOUND


def test_score_result_immutability() -> None:
    policy = MetadataScorePolicy.create()
    with pytest.raises(FrozenInstanceError):
        policy.metadata = ScoreMetadata(  # type: ignore[misc]
            policy_id="x",
            name="x",
            description="x",
            version="0",
            supported_profile="coding",
            source_oracle_id="coding.oracle.metadata",
            capabilities=ScoreCapability(),
        )


def test_engine_attaches_score_execution() -> None:
    result = ValidationEngine.with_stubs().run(_request())
    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.oracle_execution is not None
    assert result.run_context.score_execution is not None
    assert result.run_context.score_execution.policy_count == 6
    assert result.run_context.score_execution.aggregate_score == PLACEHOLDER_SCORE_VALUE
    stage = result.run_context.placeholder_results[ValidationStage.SCORING]
    assert stage.status is StageStatus.SUCCEEDED
    assert stage.data.get("policy_count") == 6


def test_scoring_does_not_import_filesystem_inspection_flags() -> None:
    for policy in default_coding_placeholder_policies():
        assert policy.metadata.capabilities.inspects_filesystem is False
        assert policy.metadata.capabilities.consumes_oracle_result is True
        assert policy.metadata.capabilities.placeholder is True
