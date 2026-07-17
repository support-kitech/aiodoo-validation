"""Unit tests for Phase 5 Oracle Framework."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ExecutionTier,
    ExitStatus,
    OracleErrorCode,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.oracle import OracleCapability, OracleError, OracleMetadata
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.oracles import (
    MetadataOracle,
    OracleEngine,
    OracleRegistry,
    PlaceholderOracle,
    placeholder_metadata,
)
from aiodoo_validation.oracles.placeholders import default_coding_placeholder_oracles
from aiodoo_validation.profiles.engine import ProfileEngine
from aiodoo_validation.resolution.stub_resolver import StubArtifactResolver
from aiodoo_validation.validation_plan import (
    PipelineStagePlaceholder,
    ProfileCapabilities,
    ValidationPlan,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def _request(*, profile: str = "coding") -> ValidationRequest:
    return ValidationRequest(
        profile_name=profile,
        base_model_ref=str(FIXTURES / "base_model"),
        adapter_ref=str(FIXTURES / "coding_adapter"),
        execution_tier=ExecutionTier.STANDARD,
        run_id="oracle-test",
    )


def _context_with_plan() -> RunContext:
    request = _request()
    context = RunContext.begin(request)
    artifact = StubArtifactResolver().resolve(context)
    assert artifact.success and artifact.bundle is not None
    with_bundle = context.with_artifact_bundle(artifact.bundle)
    profile_outcome = ProfileEngine.create_default().resolve_profile(with_bundle)
    assert profile_outcome.success
    assert profile_outcome.profile is not None
    assert profile_outcome.plan is not None
    return with_bundle.with_validation_profile(profile_outcome.profile).with_validation_plan(
        profile_outcome.plan
    )


def test_oracle_registry_registers_and_resolves() -> None:
    registry = OracleRegistry()
    oracle = MetadataOracle.create()
    registry.register(oracle)
    assert registry.contains("coding.oracle.metadata")
    assert registry.get("coding.oracle.metadata") is oracle
    assert registry.resolve("missing") is None


def test_oracle_registry_duplicate_registration_fails() -> None:
    registry = OracleRegistry()
    registry.register(MetadataOracle.create())
    with pytest.raises(OracleError) as exc_info:
        registry.register(MetadataOracle.create())
    assert exc_info.value.code is OracleErrorCode.REGISTRATION_FAILURE


def test_oracle_registry_missing_oracle() -> None:
    registry = OracleRegistry.create_default()
    with pytest.raises(OracleError) as exc_info:
        registry.get("coding.oracle.unknown")
    assert exc_info.value.code is OracleErrorCode.ORACLE_NOT_FOUND


def test_default_registry_contains_placeholder_oracles() -> None:
    registry = OracleRegistry.create_default()
    expected = {oracle.metadata.oracle_id for oracle in default_coding_placeholder_oracles()}
    assert set(registry.registered_ids()) == expected


def test_placeholder_oracle_execution_is_successful() -> None:
    from aiodoo_validation.domain.oracle import OracleContext

    context = _context_with_plan()
    plan = context.validation_plan
    assert plan is not None
    oracle = MetadataOracle.create()
    oracle_context = OracleContext(
        run_id=context.run_id,
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        protocol_major=context.protocol_major,
        protocol_minor=context.protocol_minor,
        execution_tier=context.execution_tier,
        configuration=plan.configuration,
        artifact_bundle=context.artifact_bundle,
        inference_session=context.inference_session,
    )
    result = oracle.execute(oracle_context)
    assert result.success is True
    assert result.oracle_id == "coding.oracle.metadata"
    assert result.metadata["placeholder"] is True


def test_oracle_pipeline_executes_enabled_placeholders() -> None:
    context = _context_with_plan()
    outcome = OracleEngine.create_default().execute_oracles(context)
    assert outcome.success is True
    assert outcome.execution is not None
    assert outcome.execution.oracle_count == 6
    assert outcome.execution.success_count == 6
    assert outcome.execution.failure_count == 0
    ids = tuple(result.oracle_id for result in outcome.execution.results)
    assert ids == (
        "coding.oracle.metadata",
        "coding.oracle.manifest",
        "coding.oracle.python",
        "coding.oracle.xml",
        "coding.oracle.security",
        "coding.oracle.module_structure",
    )


def test_disabled_quality_oracle_is_skipped() -> None:
    context = _context_with_plan()
    plan = context.validation_plan
    assert plan is not None
    quality = next(stage for stage in plan.oracle_pipeline if stage.stage_id.endswith("quality"))
    assert quality.enabled is False
    outcome = OracleEngine.create_default().execute_oracles(context)
    assert outcome.execution is not None
    assert "coding.oracle.quality" not in {result.oracle_id for result in outcome.execution.results}


def test_missing_plan_fails_gracefully() -> None:
    context = RunContext.begin(_request())
    outcome = OracleEngine.create_default().execute_oracles(context)
    assert outcome.success is False
    assert outcome.errors[0].code is OracleErrorCode.MISSING_PLAN


def test_unknown_oracle_in_pipeline_fails_gracefully() -> None:
    context = _context_with_plan()
    plan = context.validation_plan
    assert plan is not None
    broken = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=plan.capabilities,
        supported_artifact_types=plan.supported_artifact_types,
        supported_runtimes=plan.supported_runtimes,
        oracle_pipeline=(
            PipelineStagePlaceholder(
                stage_id="coding.oracle.missing",
                name="Missing",
                enabled=True,
                phase="oracle",
            ),
        ),
        scoring_pipeline=plan.scoring_pipeline,
        benchmark_pipeline=plan.benchmark_pipeline,
        certification_pipeline=plan.certification_pipeline,
        report_pipeline=plan.report_pipeline,
        execution_order=plan.execution_order,
        validation_stages=plan.validation_stages,
        configuration=plan.configuration,
    )
    outcome = OracleEngine.create_default().execute_oracles(context.with_validation_plan(broken))
    assert outcome.success is False
    assert outcome.errors[0].code is OracleErrorCode.ORACLE_NOT_FOUND


def test_capability_mismatch_fails() -> None:
    context = _context_with_plan()
    plan = context.validation_plan
    assert plan is not None
    disabled = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=ProfileCapabilities(supports_inference=True, supports_oracles=False),
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
    outcome = OracleEngine.create_default().execute_oracles(context.with_validation_plan(disabled))
    assert outcome.success is False
    assert outcome.errors[0].code is OracleErrorCode.CAPABILITY_MISMATCH


def test_profile_mismatch_fails() -> None:
    registry = OracleRegistry()
    registry.register(
        PlaceholderOracle(
            metadata=placeholder_metadata(
                oracle_id="coding.oracle.metadata",
                name="Wrong Profile Oracle",
                description="Mismatch fixture",
                supported_profile="planner",
            )
        )
    )
    context = _context_with_plan()
    plan = context.validation_plan
    assert plan is not None
    narrowed = ValidationPlan(
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        capabilities=plan.capabilities,
        supported_artifact_types=plan.supported_artifact_types,
        supported_runtimes=plan.supported_runtimes,
        oracle_pipeline=(
            PipelineStagePlaceholder(
                stage_id="coding.oracle.metadata",
                name="Metadata Oracle",
                enabled=True,
                phase="oracle",
            ),
        ),
        scoring_pipeline=plan.scoring_pipeline,
        benchmark_pipeline=plan.benchmark_pipeline,
        certification_pipeline=plan.certification_pipeline,
        report_pipeline=plan.report_pipeline,
        execution_order=plan.execution_order,
        validation_stages=plan.validation_stages,
        configuration=plan.configuration,
    )
    outcome = OracleEngine(registry=registry).execute_oracles(
        context.with_validation_plan(narrowed)
    )
    assert outcome.success is False
    assert outcome.errors[0].code is OracleErrorCode.PROFILE_MISMATCH


def test_oracle_result_immutability() -> None:
    oracle = MetadataOracle.create()
    with pytest.raises(FrozenInstanceError):
        oracle.metadata = OracleMetadata(  # type: ignore[misc]
            oracle_id="x",
            name="x",
            description="x",
            version="0",
            supported_profile="coding",
            capabilities=OracleCapability(),
        )


def test_engine_attaches_oracle_execution() -> None:
    result = ValidationEngine.with_stubs().run(_request())
    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.oracle_execution is not None
    assert result.run_context.oracle_execution.oracle_count == 6
    stage = result.run_context.placeholder_results[ValidationStage.RUN_VALIDATION]
    assert stage.status is StageStatus.SUCCEEDED
    assert stage.data.get("oracle_count") == 6


def test_engine_oracle_failure_does_not_crash() -> None:
    request = _request()
    context = RunContext.begin(request)
    # Direct engine call with incomplete context via custom runner path
    outcome = OracleEngine.create_default().execute_oracles(context)
    assert outcome.success is False
    engine_result = ValidationEngine.with_stubs().run(request)
    assert engine_result.exit_status is ExitStatus.NOT_CERTIFIED
    assert engine_result.run_context.oracle_execution is not None
