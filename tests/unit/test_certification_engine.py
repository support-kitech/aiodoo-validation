"""Unit tests for Phase 8 Certification Engine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiodoo_validation.benchmark import BenchmarkEngine
from aiodoo_validation.benchmark.ids import CODING_BENCHMARK_IDS_ENABLED, CODING_BENCHMARK_METADATA
from aiodoo_validation.certification import (
    CertificationEngine,
    CertificationRegistry,
    MetadataCertificationPolicy,
)
from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_IDS_ENABLED,
    CODING_CERTIFICATION_METADATA,
    CODING_CERTIFICATION_TO_BENCHMARK,
    PLACEHOLDER_CERTIFICATION_LEVEL,
    PLACEHOLDER_CERTIFICATION_SCORE,
    PLACEHOLDER_CERTIFIED,
)
from aiodoo_validation.certification.policies import default_coding_placeholder_policies
from aiodoo_validation.domain.certification import (
    CertificationCapability,
    CertificationContext,
    CertificationError,
    CertificationMetadata,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    CertificationErrorCode,
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
        run_id="certification-test",
    )


def _context_ready_for_certification() -> RunContext:
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
    with_score = with_oracle.with_score_execution(score_outcome.execution)
    benchmark_outcome = BenchmarkEngine.create_default().benchmark(with_score)
    assert benchmark_outcome.success and benchmark_outcome.execution is not None
    return with_score.with_benchmark_execution(benchmark_outcome.execution)


def test_certification_ids_map_to_benchmark_ids() -> None:
    for policy_id in CODING_CERTIFICATION_IDS_ENABLED:
        benchmark_id = CODING_CERTIFICATION_TO_BENCHMARK[policy_id]
        assert benchmark_id in CODING_BENCHMARK_IDS_ENABLED
        assert policy_id.replace(".certification.", ".benchmark.") == benchmark_id


def test_certification_registry_registers_and_resolves() -> None:
    registry = CertificationRegistry()
    policy = MetadataCertificationPolicy.create()
    registry.register(policy)
    assert registry.contains(CODING_CERTIFICATION_METADATA)
    assert registry.get(CODING_CERTIFICATION_METADATA) is policy


def test_certification_registry_duplicate_fails() -> None:
    registry = CertificationRegistry()
    registry.register(MetadataCertificationPolicy.create())
    with pytest.raises(CertificationError) as exc_info:
        registry.register(MetadataCertificationPolicy.create())
    assert exc_info.value.code is CertificationErrorCode.REGISTRATION_FAILURE


def test_certification_registry_missing_policy() -> None:
    registry = CertificationRegistry.create_default()
    with pytest.raises(CertificationError) as exc_info:
        registry.get("coding.certification.unknown")
    assert exc_info.value.code is CertificationErrorCode.POLICY_NOT_FOUND


def test_default_registry_contains_placeholder_policies() -> None:
    registry = CertificationRegistry.create_default()
    expected = {policy.metadata.policy_id for policy in default_coding_placeholder_policies()}
    assert set(registry.registered_ids()) == expected


def test_placeholder_policy_returns_deterministic_values() -> None:
    context = _context_ready_for_certification()
    assert context.benchmark_execution is not None
    benchmark_result = next(
        result
        for result in context.benchmark_execution.results
        if result.policy_id == CODING_BENCHMARK_METADATA
    )
    plan = context.validation_plan
    assert plan is not None
    certification_context = CertificationContext(
        run_id=context.run_id,
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        protocol_major=context.protocol_major,
        protocol_minor=context.protocol_minor,
        execution_tier=context.execution_tier,
        benchmark_result=benchmark_result,
        benchmark_execution=context.benchmark_execution,
        configuration=plan.configuration,
    )
    result = MetadataCertificationPolicy.create().certify(certification_context)
    assert result.success is True
    assert result.certified is PLACEHOLDER_CERTIFIED
    assert result.certification_score == PLACEHOLDER_CERTIFICATION_SCORE
    assert result.certification_level == PLACEHOLDER_CERTIFICATION_LEVEL
    assert result.source_benchmark_policy_id == CODING_BENCHMARK_METADATA


def test_certification_pipeline_executes_enabled_policies() -> None:
    context = _context_ready_for_certification()
    outcome = CertificationEngine.create_default().certify(context)
    assert outcome.success is True
    assert outcome.execution is not None
    assert outcome.execution.policy_count == 6
    assert outcome.execution.success_count == 6
    assert outcome.execution.certified_count == 6
    assert outcome.execution.overall_certified is True
    assert outcome.execution.aggregate_certification_score == PLACEHOLDER_CERTIFICATION_SCORE
    ids = tuple(result.policy_id for result in outcome.execution.results)
    assert ids == CODING_CERTIFICATION_IDS_ENABLED


def test_disabled_quality_certification_is_skipped() -> None:
    context = _context_ready_for_certification()
    plan = context.validation_plan
    assert plan is not None
    quality = next(
        stage for stage in plan.certification_pipeline if stage.stage_id.endswith("quality")
    )
    assert quality.enabled is False
    outcome = CertificationEngine.create_default().certify(context)
    assert outcome.execution is not None
    assert "coding.certification.quality" not in {
        result.policy_id for result in outcome.execution.results
    }


def test_missing_benchmark_results_fails_gracefully() -> None:
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
    outcome = CertificationEngine.create_default().certify(ready)
    assert outcome.success is False
    assert outcome.errors[0].code is CertificationErrorCode.MISSING_BENCHMARK_RESULTS


def test_capability_mismatch_fails() -> None:
    context = _context_ready_for_certification()
    plan = context.validation_plan
    assert plan is not None
    disabled = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=ProfileCapabilities(
            supports_inference=True,
            supports_oracles=True,
            supports_scoring=True,
            supports_benchmark=True,
            supports_certification=False,
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
    outcome = CertificationEngine.create_default().certify(context.with_validation_plan(disabled))
    assert outcome.success is False
    assert outcome.errors[0].code is CertificationErrorCode.CAPABILITY_MISMATCH


def test_unknown_policy_in_pipeline_fails() -> None:
    context = _context_ready_for_certification()
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
        benchmark_pipeline=plan.benchmark_pipeline,
        certification_pipeline=(
            PipelineStagePlaceholder(
                stage_id="coding.certification.missing",
                name="Missing",
                enabled=True,
                phase="certification",
            ),
        ),
        report_pipeline=plan.report_pipeline,
        execution_order=plan.execution_order,
        validation_stages=plan.validation_stages,
        configuration=plan.configuration,
    )
    outcome = CertificationEngine.create_default().certify(context.with_validation_plan(broken))
    assert outcome.success is False
    assert outcome.errors[0].code is CertificationErrorCode.POLICY_NOT_FOUND


def test_certification_result_immutability() -> None:
    policy = MetadataCertificationPolicy.create()
    with pytest.raises(FrozenInstanceError):
        policy.metadata = CertificationMetadata(  # type: ignore[misc]
            policy_id="x",
            name="x",
            description="x",
            version="0",
            supported_profile="coding",
            source_benchmark_policy_id="coding.benchmark.metadata",
            capabilities=CertificationCapability(),
        )


def test_engine_attaches_certification_execution() -> None:
    result = ValidationEngine.with_stubs().run(_request())
    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.benchmark_execution is not None
    assert result.run_context.certification_execution is not None
    assert result.run_context.certification_execution.policy_count == 6
    assert result.run_context.certification_execution.overall_certified is True
    stage = result.run_context.placeholder_results[ValidationStage.CERTIFICATION]
    assert stage.status is StageStatus.SUCCEEDED
    assert stage.data.get("policy_count") == 6


def test_certification_capabilities_forbid_filesystem_and_thresholds() -> None:
    for policy in default_coding_placeholder_policies():
        assert policy.metadata.capabilities.inspects_filesystem is False
        assert policy.metadata.capabilities.applies_thresholds is False
        assert policy.metadata.capabilities.consumes_benchmark_result is True
        assert policy.metadata.capabilities.placeholder is True
