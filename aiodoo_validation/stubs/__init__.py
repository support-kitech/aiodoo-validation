"""Stub implementations for remaining pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import StageStatus, ValidationStage
from aiodoo_validation.domain.stage import PlaceholderStageResult
from aiodoo_validation.inference.stub_runner import StubInferenceRunner
from aiodoo_validation.oracles import OracleEngine
from aiodoo_validation.ports import (
    ArtifactResolverPort,
    BenchmarkEnginePort,
    CertificationEnginePort,
    InferenceRunnerPort,
    OracleRunnerPort,
    ProfileEnginePort,
    ReportGeneratorPort,
    ScoringEnginePort,
)
from aiodoo_validation.profiles import ProfileEngine
from aiodoo_validation.resolution.stub_resolver import StubArtifactResolver
from aiodoo_validation.scoring import ScoringEngine


def _stub_result(stage: ValidationStage, *, message: str, **data: object) -> PlaceholderStageResult:
    return PlaceholderStageResult(
        stage=stage,
        status=StageStatus.SUCCEEDED,
        message=message,
        data=MappingProxyType(dict(data)),
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
    oracle_runner: OracleRunnerPort
    scoring_engine: ScoringEnginePort
    benchmark_engine: BenchmarkEnginePort
    certification_engine: CertificationEnginePort
    report_generator: ReportGeneratorPort

    @classmethod
    def create(cls) -> StubPipelineComponents:
        return cls(
            artifact_resolver=StubArtifactResolver(),
            profile_engine=ProfileEngine.create_default(),
            inference_runner=StubInferenceRunner.create(),
            oracle_runner=OracleEngine.create_default(),
            scoring_engine=ScoringEngine.create_default(),
            benchmark_engine=StubBenchmarkEngine(),
            certification_engine=StubCertificationEngine(),
            report_generator=StubReportGenerator(),
        )
