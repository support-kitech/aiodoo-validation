"""Unit tests for Phase 9 Report Generator."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiodoo_validation.benchmark import BenchmarkEngine
from aiodoo_validation.certification import CertificationEngine
from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_IDS_ENABLED,
    CODING_CERTIFICATION_METADATA,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ExecutionTier,
    ExitStatus,
    ReportErrorCode,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.report import (
    ReportCapability,
    ReportContext,
    ReportError,
    ReportMetadata,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.oracles import OracleEngine
from aiodoo_validation.profiles.engine import ProfileEngine
from aiodoo_validation.reporting import MetadataReportTemplate, ReportGenerator, ReportRegistry
from aiodoo_validation.reporting.ids import (
    CODING_REPORT_IDS_ENABLED,
    CODING_REPORT_METADATA,
    CODING_REPORT_TO_CERTIFICATION,
    PLACEHOLDER_REPORT_STATUS,
    PLACEHOLDER_REPORT_SUMMARY,
)
from aiodoo_validation.reporting.templates import default_coding_placeholder_templates
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
        run_id="report-test",
    )


def _context_ready_for_reports() -> RunContext:
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
    with_benchmark = with_score.with_benchmark_execution(benchmark_outcome.execution)
    certification_outcome = CertificationEngine.create_default().certify(with_benchmark)
    assert certification_outcome.success and certification_outcome.execution is not None
    return with_benchmark.with_certification_execution(certification_outcome.execution)


def test_report_ids_map_to_certification_ids() -> None:
    for template_id in CODING_REPORT_IDS_ENABLED:
        certification_id = CODING_REPORT_TO_CERTIFICATION[template_id]
        assert certification_id in CODING_CERTIFICATION_IDS_ENABLED
        assert template_id.replace(".report.", ".certification.") == certification_id


def test_report_registry_registers_and_resolves() -> None:
    registry = ReportRegistry()
    template = MetadataReportTemplate.create()
    registry.register(template)
    assert registry.contains(CODING_REPORT_METADATA)
    assert registry.get(CODING_REPORT_METADATA) is template


def test_report_registry_duplicate_fails() -> None:
    registry = ReportRegistry()
    registry.register(MetadataReportTemplate.create())
    with pytest.raises(ReportError) as exc_info:
        registry.register(MetadataReportTemplate.create())
    assert exc_info.value.code is ReportErrorCode.REGISTRATION_FAILURE


def test_report_registry_missing_template() -> None:
    registry = ReportRegistry.create_default()
    with pytest.raises(ReportError) as exc_info:
        registry.get("coding.report.unknown")
    assert exc_info.value.code is ReportErrorCode.TEMPLATE_NOT_FOUND


def test_default_registry_contains_placeholder_templates() -> None:
    registry = ReportRegistry.create_default()
    templates = default_coding_placeholder_templates()
    expected = {template.metadata.template_id for template in templates}
    assert set(registry.registered_ids()) == expected


def test_placeholder_template_returns_deterministic_values() -> None:
    context = _context_ready_for_reports()
    assert context.certification_execution is not None
    certification_result = next(
        result
        for result in context.certification_execution.results
        if result.policy_id == CODING_CERTIFICATION_METADATA
    )
    plan = context.validation_plan
    assert plan is not None
    report_context = ReportContext(
        run_id=context.run_id,
        profile_name=plan.profile_name,
        plan_digest=plan.plan_digest,
        protocol_major=context.protocol_major,
        protocol_minor=context.protocol_minor,
        execution_tier=context.execution_tier,
        certification_result=certification_result,
        certification_execution=context.certification_execution,
        configuration=plan.configuration,
    )
    result = MetadataReportTemplate.create().generate(report_context)
    assert result.success is True
    assert result.status == PLACEHOLDER_REPORT_STATUS
    assert result.summary == PLACEHOLDER_REPORT_SUMMARY
    assert len(result.sections) == 1
    assert result.source_certification_policy_id == CODING_CERTIFICATION_METADATA


def test_report_pipeline_executes_enabled_templates() -> None:
    context = _context_ready_for_reports()
    outcome = ReportGenerator.create_default().generate_report(context)
    assert outcome.success is True
    assert outcome.execution is not None
    assert outcome.execution.template_count == 6
    assert outcome.execution.success_count == 6
    assert outcome.execution.overall_status == PLACEHOLDER_REPORT_STATUS
    ids = tuple(result.template_id for result in outcome.execution.results)
    assert ids == CODING_REPORT_IDS_ENABLED


def test_disabled_quality_report_is_skipped() -> None:
    context = _context_ready_for_reports()
    plan = context.validation_plan
    assert plan is not None
    quality = next(stage for stage in plan.report_pipeline if stage.stage_id.endswith("quality"))
    assert quality.enabled is False
    outcome = ReportGenerator.create_default().generate_report(context)
    assert outcome.execution is not None
    assert "coding.report.quality" not in {
        result.template_id for result in outcome.execution.results
    }


def test_missing_certification_results_fails_gracefully() -> None:
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
    outcome = ReportGenerator.create_default().generate_report(ready)
    assert outcome.success is False
    assert outcome.errors[0].code is ReportErrorCode.MISSING_CERTIFICATION_RESULTS


def test_capability_mismatch_fails() -> None:
    context = _context_ready_for_reports()
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
            supports_certification=True,
            supports_reports=False,
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
    outcome = ReportGenerator.create_default().generate_report(
        context.with_validation_plan(disabled)
    )
    assert outcome.success is False
    assert outcome.errors[0].code is ReportErrorCode.CAPABILITY_MISMATCH


def test_unknown_template_in_pipeline_fails() -> None:
    context = _context_ready_for_reports()
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
        certification_pipeline=plan.certification_pipeline,
        report_pipeline=(
            PipelineStagePlaceholder(
                stage_id="coding.report.missing",
                name="Missing",
                enabled=True,
                phase="report",
            ),
        ),
        execution_order=plan.execution_order,
        validation_stages=plan.validation_stages,
        configuration=plan.configuration,
    )
    outcome = ReportGenerator.create_default().generate_report(context.with_validation_plan(broken))
    assert outcome.success is False
    assert outcome.errors[0].code is ReportErrorCode.TEMPLATE_NOT_FOUND


def test_report_result_immutability() -> None:
    template = MetadataReportTemplate.create()
    with pytest.raises(FrozenInstanceError):
        template.metadata = ReportMetadata(  # type: ignore[misc]
            template_id="x",
            name="x",
            description="x",
            version="0",
            supported_profile="coding",
            source_certification_policy_id="coding.certification.metadata",
            capabilities=ReportCapability(),
        )


def test_engine_attaches_report_execution() -> None:
    result = ValidationEngine.with_stubs().run(_request())
    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.certification_execution is not None
    assert result.run_context.report_execution is not None
    assert result.run_context.report_execution.template_count == 6
    assert result.run_context.report_execution.overall_status == PLACEHOLDER_REPORT_STATUS
    stage = result.run_context.placeholder_results[ValidationStage.REPORT]
    assert stage.status is StageStatus.SUCCEEDED
    assert stage.data.get("template_count") == 6


def test_report_capabilities_forbid_filesystem_and_rendering() -> None:
    for template in default_coding_placeholder_templates():
        assert template.metadata.capabilities.inspects_filesystem is False
        assert template.metadata.capabilities.renders_output is False
        assert template.metadata.capabilities.consumes_certification_result is True
        assert template.metadata.capabilities.placeholder is True
