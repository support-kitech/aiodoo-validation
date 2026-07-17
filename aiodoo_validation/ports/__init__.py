"""Port interfaces for validation pipeline collaborators."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.stage import PlaceholderStageResult
from aiodoo_validation.ports.artifact_resolver import ArtifactResolverPort
from aiodoo_validation.ports.inference_runner import InferenceRunnerPort
from aiodoo_validation.ports.oracle_runner import OracleRunnerPort
from aiodoo_validation.ports.profile_engine import ProfileEnginePort

__all__ = [
    "ArtifactResolverPort",
    "BenchmarkEnginePort",
    "CertificationEnginePort",
    "InferenceRunnerPort",
    "OracleRunnerPort",
    "ProfileEnginePort",
    "ReportGeneratorPort",
    "ScoringEnginePort",
    "ValidationRunnerPort",
]


class ValidationRunnerPort(Protocol):
    """
    Legacy stub port for RUN_VALIDATION (Phase 0–4).

    Phase 5 uses ``OracleRunnerPort`` for real oracle orchestration.
    Retained for compatibility with residual stub wiring.
    """

    def run_validation(self, context: RunContext) -> PlaceholderStageResult: ...


class ScoringEnginePort(Protocol):
    """Aggregate validation scores (Phase 6+)."""

    def score(self, context: RunContext) -> PlaceholderStageResult: ...


class BenchmarkEnginePort(Protocol):
    """Run comparative benchmarks (Phase 7+)."""

    def benchmark(self, context: RunContext) -> PlaceholderStageResult: ...


class CertificationEnginePort(Protocol):
    """Apply certification policy (Phase 8+)."""

    def certify(self, context: RunContext) -> PlaceholderStageResult: ...


class ReportGeneratorPort(Protocol):
    """Emit Validation Protocol V1 reports (Phase 9+)."""

    def generate_report(self, context: RunContext) -> PlaceholderStageResult: ...
