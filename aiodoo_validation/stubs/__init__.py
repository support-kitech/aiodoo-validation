"""Stub implementations for Phase 0/1 pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import StageStatus, ValidationStage
from aiodoo_validation.domain.stage import PlaceholderStageResult
from aiodoo_validation.ports import (
    ArtifactResolverPort,
    BenchmarkEnginePort,
    CertificationEnginePort,
    InferenceRunnerPort,
    ProfileEnginePort,
    ReportGeneratorPort,
    ScoringEnginePort,
    ValidationRunnerPort,
)
from aiodoo_validation.resolution.stub_resolver import StubArtifactResolver


def _stub_result(stage: ValidationStage, *, message: str, **data: object) -> PlaceholderStageResult:
    return PlaceholderStageResult(
        stage=stage,
        status=StageStatus.SUCCEEDED,
        message=message,
        data=MappingProxyType(dict(data)),
    )


class StubProfileEngine:
    """Placeholder profile engine."""

    def resolve_profile(self, context: RunContext) -> PlaceholderStageResult:
        return _stub_result(
            ValidationStage.RESOLVE_PROFILE,
            message="stub profile resolution",
            profile_name=context.request.profile_name,
            odoo_versions=context.request.odoo_versions,
            stub=True,
        )


class StubInferenceRunner:
    """Placeholder inference runner."""

    def initialize(self, context: RunContext) -> PlaceholderStageResult:
        return _stub_result(
            ValidationStage.INITIALIZE_INFERENCE,
            message="stub inference initialization",
            execution_tier=context.execution_tier.value,
            stub=True,
        )


class StubValidationRunner:
    """Placeholder validation/oracle runner."""

    def run_validation(self, context: RunContext) -> PlaceholderStageResult:
        return _stub_result(
            ValidationStage.RUN_VALIDATION,
            message="stub validation execution",
            checks_planned=0,
            stub=True,
        )


class StubScoringEngine:
    """Placeholder scoring engine."""

    def score(self, context: RunContext) -> PlaceholderStageResult:
        return _stub_result(
            ValidationStage.SCORING,
            message="stub scoring",
            validation_verdict="not_evaluated",
            stub=True,
        )


class StubBenchmarkEngine:
    """Placeholder benchmark engine."""

    def benchmark(self, context: RunContext) -> PlaceholderStageResult:
        return _stub_result(
            ValidationStage.BENCHMARK,
            message="stub benchmark",
            benchmark_verdict="not_evaluated",
            stub=True,
        )


class StubCertificationEngine:
    """Placeholder certification engine."""

    def certify(self, context: RunContext) -> PlaceholderStageResult:
        return _stub_result(
            ValidationStage.CERTIFICATION,
            message="stub certification",
            certification_status="not_certified",
            stub=True,
        )


class StubReportGenerator:
    """Placeholder report generator."""

    def generate_report(self, context: RunContext) -> PlaceholderStageResult:
        return _stub_result(
            ValidationStage.REPORT,
            message="stub report generation",
            protocol_major=context.protocol_major,
            protocol_minor=context.protocol_minor,
            report_generated=False,
            stub=True,
        )


@dataclass(frozen=True, slots=True)
class StubPipelineComponents:
    """Bundle of stub ports for dependency injection."""

    artifact_resolver: ArtifactResolverPort
    profile_engine: ProfileEnginePort
    inference_runner: InferenceRunnerPort
    validation_runner: ValidationRunnerPort
    scoring_engine: ScoringEnginePort
    benchmark_engine: BenchmarkEnginePort
    certification_engine: CertificationEnginePort
    report_generator: ReportGeneratorPort

    @classmethod
    def create(cls) -> StubPipelineComponents:
        return cls(
            artifact_resolver=StubArtifactResolver(),
            profile_engine=StubProfileEngine(),
            inference_runner=StubInferenceRunner(),
            validation_runner=StubValidationRunner(),
            scoring_engine=StubScoringEngine(),
            benchmark_engine=StubBenchmarkEngine(),
            certification_engine=StubCertificationEngine(),
            report_generator=StubReportGenerator(),
        )
