"""Stub implementations for remaining pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.benchmark import BenchmarkEngine
from aiodoo_validation.certification import CertificationEngine
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
from aiodoo_validation.reporting import ReportGenerator
from aiodoo_validation.resolution.stub_resolver import StubArtifactResolver
from aiodoo_validation.scoring import ScoringEngine


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
            benchmark_engine=BenchmarkEngine.create_default(),
            certification_engine=CertificationEngine.create_default(),
            report_generator=ReportGenerator.create_default(),
        )
