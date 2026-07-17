"""Unit tests for Phase 7 Benchmark Engine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiodoo_validation.benchmark import (
    BenchmarkEngine,
    BenchmarkRegistry,
    MetadataBenchmarkPolicy,
)
from aiodoo_validation.benchmark.ids import (
    CODING_BENCHMARK_IDS_ENABLED,
    CODING_BENCHMARK_METADATA,
    CODING_BENCHMARK_TO_SCORE,
    PLACEHOLDER_BENCHMARK_PASS,
    PLACEHOLDER_BENCHMARK_RANK,
    PLACEHOLDER_BENCHMARK_SCORE,
)
from aiodoo_validation.benchmark.policies import default_coding_placeholder_policies
from aiodoo_validation.domain.benchmark import (
    BenchmarkCapability,
    BenchmarkContext,
    BenchmarkError,
    BenchmarkMetadata,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    BenchmarkErrorCode,
    ExecutionTier,
    ExitStatus,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.oracles import OracleEngine
from aiodoo_validation.profiles.engine import ProfileEngine
from aiodoo_validation.resolution.stub_resolver import StubArtifactResolver
from aiodoo_validation.scoring import ScoringEngine
from aiodoo_validation.scoring.ids import CODING_SCORE_IDS_ENABLED, CODING_SCORE_METADATA
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
        run_id="benchmark-test",
    )


def _context_ready_for_benchmark() -> RunContext:
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
    with_oracle = with_profile.with_oracle_execution(oracle_outcome.execution)
    score_outcome = ScoringEngine.create_default().score(with_oracle)
    assert score_outcome.success and score_outcome.execution is not None
    return with_oracle.with_score_execution(score_outcome.execution)


def test_benchmark_ids_map_to_score_ids() -> None:
    for policy_id in CODING_BENCHMARK_IDS_ENABLED:
        score_id = CODING_BENCHMARK_TO_SCORE[policy_id]
        assert score_id in CODING_SCORE_IDS_ENABLED
        assert policy_id.replace(".benchmark.", ".score.") == score_id


def test_benchmark_registry_registers_and_resolves() -> None:
    registry = BenchmarkRegistry()
    policy = MetadataBenchmarkPolicy.create()
    registry.register(policy)
    assert registry.contains(CODING_BENCHMARK_METADATA)
    assert registry.get(CODING_BENCHMARK_METADATA) is policy


def test_benchmark_registry_duplicate_fails() -> None:
    registry = BenchmarkRegistry()
    registry.register(MetadataBenchmarkPolicy.create())
    with pytest.raises(BenchmarkError) as exc_info:
        registry.register(MetadataBenchmarkPolicy.create())
    assert exc_info.value.code is BenchmarkErrorCode.REGISTRATION_FAILURE


def test_benchmark_registry_missing_policy() -> None:
    registry = BenchmarkRegistry.create_default()
    with pytest.raises(BenchmarkError) as exc_info:
        registry.get("coding.benchmark.unknown")
    assert exc_info.value.code is BenchmarkErrorCode.POLICY_NOT_FOUND


def test_default_registry_contains_placeholder_policies() -> None:
    registry = BenchmarkRegistry.create_default()
    expected = {policy.metadata.policy_id for policy in default_coding_placeholder_policies()}
    assert set(registry.registered_ids()) == expected


def test_placeholder_policy_returns_deterministic_values() -> None:
    context = _context_ready_for_benchmark()
    assert context.score_execution is not None
    score_result = next(
        result
        for result in context.score_execution.results
        if result.policy_id == CODING_SCORE_METADATA
    )
    plan = context.validation_plan
    assert plan is not None
    benchmark_context = BenchmarkContext(
        run_id=context.run_id,
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        protocol_major=context.protocol_major,
        protocol_minor=context.protocol_minor,
        execution_tier=context.execution_tier,
        score_result=score_result,
        score_execution=context.score_execution,
        configuration=plan.configuration,
    )
    result = MetadataBenchmarkPolicy.create().benchmark(benchmark_context)
    assert result.success is True
    assert result.benchmark_score == PLACEHOLDER_BENCHMARK_SCORE
    assert result.benchmark_pass is PLACEHOLDER_BENCHMARK_PASS
    assert result.benchmark_rank == PLACEHOLDER_BENCHMARK_RANK
    assert result.source_score_policy_id == CODING_SCORE_METADATA


def test_benchmark_pipeline_executes_enabled_policies() -> None:
    context = _context_ready_for_benchmark()
    outcome = BenchmarkEngine.create_default().benchmark(context)
    assert outcome.success is True
    assert outcome.execution is not None
    assert outcome.execution.policy_count == 6
    assert outcome.execution.success_count == 6
    assert outcome.execution.aggregate_benchmark_score == PLACEHOLDER_BENCHMARK_SCORE
    ids = tuple(result.policy_id for result in outcome.execution.results)
    assert ids == CODING_BENCHMARK_IDS_ENABLED


def test_disabled_quality_benchmark_is_skipped() -> None:
    context = _context_ready_for_benchmark()
    plan = context.validation_plan
    assert plan is not None
    quality = next(stage for stage in plan.benchmark_pipeline if stage.stage_id.endswith("quality"))
    assert quality.enabled is False
    outcome = BenchmarkEngine.create_default().benchmark(context)
    assert outcome.execution is not None
    assert "coding.benchmark.quality" not in {
        result.policy_id for result in outcome.execution.results
    }


def test_missing_score_results_fails_gracefully() -> None:
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
    outcome = BenchmarkEngine.create_default().benchmark(ready)
    assert outcome.success is False
    assert outcome.errors[0].code is BenchmarkErrorCode.MISSING_SCORE_RESULTS


def test_capability_mismatch_fails() -> None:
    context = _context_ready_for_benchmark()
    plan = context.validation_plan
    assert plan is not None
    disabled = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=ProfileCapabilities(
            supports_inference=True,
            supports_oracles=True,
            supports_scoring=True,
            supports_benchmark=False,
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
    outcome = BenchmarkEngine.create_default().benchmark(context.with_validation_plan(disabled))
    assert outcome.success is False
    assert outcome.errors[0].code is BenchmarkErrorCode.CAPABILITY_MISMATCH


def test_unknown_policy_in_pipeline_fails() -> None:
    context = _context_ready_for_benchmark()
    plan = context.validation_plan
    assert plan is not None
    broken = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=plan.capabilities,
        supported_artifact_types=plan.supported_artifact_types,
        supported_runtimes=plan.supported_runtimes,
        oracle_pipeline=plan.oracle_pipeline,
        scoring_pipeline=plan.scoring_pipeline,
        benchmark_pipeline=(
            PipelineStagePlaceholder(
                stage_id="coding.benchmark.missing",
                name="Missing",
                enabled=True,
                phase="benchmark",
            ),
        ),
        certification_pipeline=plan.certification_pipeline,
        report_pipeline=plan.report_pipeline,
        execution_order=plan.execution_order,
        validation_stages=plan.validation_stages,
        configuration=plan.configuration,
    )
    outcome = BenchmarkEngine.create_default().benchmark(context.with_validation_plan(broken))
    assert outcome.success is False
    assert outcome.errors[0].code is BenchmarkErrorCode.POLICY_NOT_FOUND


def test_benchmark_result_immutability() -> None:
    policy = MetadataBenchmarkPolicy.create()
    with pytest.raises(FrozenInstanceError):
        policy.metadata = BenchmarkMetadata(  # type: ignore[misc]
            policy_id="x",
            name="x",
            description="x",
            version="0",
            supported_profile="coding",
            source_score_policy_id="coding.score.metadata",
            capabilities=BenchmarkCapability(),
        )


def test_engine_attaches_benchmark_execution() -> None:
    result = ValidationEngine.with_stubs().run(_request())
    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.score_execution is not None
    assert result.run_context.benchmark_execution is not None
    assert result.run_context.benchmark_execution.policy_count == 6
    assert (
        result.run_context.benchmark_execution.aggregate_benchmark_score
        == PLACEHOLDER_BENCHMARK_SCORE
    )
    stage = result.run_context.placeholder_results[ValidationStage.BENCHMARK]
    assert stage.status is StageStatus.SUCCEEDED
    assert stage.data.get("policy_count") == 6


def test_benchmark_capabilities_forbid_filesystem() -> None:
    for policy in default_coding_placeholder_policies():
        assert policy.metadata.capabilities.inspects_filesystem is False
        assert policy.metadata.capabilities.uses_datasets is False
        assert policy.metadata.capabilities.consumes_score_result is True
        assert policy.metadata.capabilities.placeholder is True
