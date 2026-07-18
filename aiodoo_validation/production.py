"""Production DI bundle for the filesystem CLI validation path."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.benchmark import BenchmarkEngine
from aiodoo_validation.benchmark.production import default_production_benchmark_policies
from aiodoo_validation.benchmark.registry import BenchmarkRegistry
from aiodoo_validation.certification import CertificationEngine
from aiodoo_validation.certification.production import default_production_certification_policies
from aiodoo_validation.certification.registry import CertificationRegistry
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import SupportedValidationProfile
from aiodoo_validation.domain.inference import (
    GenerationRequest,
    InferenceGenerationOutcome,
    InferenceInitializationOutcome,
)
from aiodoo_validation.execution import requires_real_inference
from aiodoo_validation.inference import RealInferenceRunner
from aiodoo_validation.inference.runtime.mock import MockModelRuntime
from aiodoo_validation.inference.runtime.qwen import QwenModelRuntime
from aiodoo_validation.inference.stub_runner import StubInferenceRunner
from aiodoo_validation.oracles import OracleEngine
from aiodoo_validation.oracles.registry import OracleRegistry
from aiodoo_validation.oracles.structural import default_production_oracles
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
from aiodoo_validation.reporting import ReportGenerator
from aiodoo_validation.reporting.production import default_production_report_templates
from aiodoo_validation.reporting.registry import ReportRegistry
from aiodoo_validation.resolution.filesystem import FilesystemArtifactResolver
from aiodoo_validation.scoring import ScoringEngine
from aiodoo_validation.scoring.production import default_production_score_policies
from aiodoo_validation.scoring.registry import ScoringRegistry


class TierAwareInferenceRunner:
    """
    Select inference backend by execution tier.

    - standard: stub (framework wiring only)
    - smoke/full: try Qwen HF; on dependency/load failure fall back to mock
    """

    def __init__(self) -> None:
        self._stub = StubInferenceRunner.create()
        self._qwen = RealInferenceRunner(runtime=QwenModelRuntime())
        self._mock = RealInferenceRunner(runtime=MockModelRuntime())
        self._active: InferenceRunnerPort | None = None

    def initialize(self, context: RunContext) -> InferenceInitializationOutcome:
        if not requires_real_inference(context.execution_tier):
            self._active = self._stub
            return self._stub.initialize(context)

        outcome = self._qwen.initialize(context)
        if outcome.success:
            self._active = self._qwen
            return outcome

        fallback = self._mock.initialize(context)
        if fallback.success:
            self._active = self._mock
            warnings = tuple(err.message for err in outcome.errors)
            return InferenceInitializationOutcome(
                success=True,
                message=(
                    "Qwen runtime unavailable; using mock inference for smoke/full validation. "
                    + (" ".join(warnings) if warnings else "")
                ).strip(),
                session=fallback.session,
                warnings=warnings,
            )
        self._active = None
        return outcome

    def generate(
        self,
        context: RunContext,
        request: GenerationRequest,
    ) -> InferenceGenerationOutcome:
        runner = self._active or self._stub
        return runner.generate(context, request)

    def shutdown(self, context: RunContext) -> None:
        for runner in (self._stub, self._qwen, self._mock):
            runner.shutdown(context)
        self._active = None


def _register_profile_stack(
    *,
    profile: str,
    oracle_registry: OracleRegistry,
    score_registry: ScoringRegistry,
    bench_registry: BenchmarkRegistry,
    cert_registry: CertificationRegistry,
    report_registry: ReportRegistry,
) -> None:
    for oracle in default_production_oracles(profile=profile):
        oracle_registry.register(oracle)
    for score_policy in default_production_score_policies(profile=profile):
        score_registry.register(score_policy)
    for bench_policy in default_production_benchmark_policies(profile=profile):
        bench_registry.register(bench_policy)
    for cert_policy in default_production_certification_policies(profile=profile):
        cert_registry.register(cert_policy)
    for template in default_production_report_templates(profile=profile):
        report_registry.register(template)


@dataclass(frozen=True, slots=True)
class ProductionPipelineComponents:
    """Ports wired for production filesystem validation."""

    artifact_resolver: ArtifactResolverPort
    profile_engine: ProfileEnginePort
    inference_runner: InferenceRunnerPort
    oracle_runner: OracleRunnerPort
    scoring_engine: ScoringEnginePort
    benchmark_engine: BenchmarkEnginePort
    certification_engine: CertificationEnginePort
    report_generator: ReportGeneratorPort

    @classmethod
    def create(cls) -> ProductionPipelineComponents:
        oracle_registry = OracleRegistry()
        score_registry = ScoringRegistry()
        bench_registry = BenchmarkRegistry()
        cert_registry = CertificationRegistry()
        report_registry = ReportRegistry()

        for profile in SupportedValidationProfile:
            _register_profile_stack(
                profile=profile.value,
                oracle_registry=oracle_registry,
                score_registry=score_registry,
                bench_registry=bench_registry,
                cert_registry=cert_registry,
                report_registry=report_registry,
            )

        return cls(
            artifact_resolver=FilesystemArtifactResolver.create_default(),
            profile_engine=ProfileEngine.create_default(),
            inference_runner=TierAwareInferenceRunner(),
            oracle_runner=OracleEngine(registry=oracle_registry),
            scoring_engine=ScoringEngine(registry=score_registry),
            benchmark_engine=BenchmarkEngine(registry=bench_registry),
            certification_engine=CertificationEngine(registry=cert_registry),
            report_generator=ReportGenerator(registry=report_registry),
        )


__all__ = ["ProductionPipelineComponents", "TierAwareInferenceRunner"]
