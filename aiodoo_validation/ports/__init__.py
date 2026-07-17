"""Port interfaces for validation pipeline collaborators."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.stage import PlaceholderStageResult
from aiodoo_validation.ports.artifact_resolver import ArtifactResolverPort
from aiodoo_validation.ports.inference_runner import InferenceRunnerPort

__all__ = [
    "ArtifactResolverPort",
    "BenchmarkEnginePort",
    "CertificationEnginePort",
    "InferenceRunnerPort",
    "ProfileEnginePort",
    "ReportGeneratorPort",
    "ScoringEnginePort",
    "ValidationRunnerPort",
]


class ProfileEnginePort(Protocol):
    """Select and plan validation profile checks (Phase 4+)."""

    def resolve_profile(self, context: RunContext) -> PlaceholderStageResult: ...


class ValidationRunnerPort(Protocol):
    """Execute validation/oracle phase (Phase 5+)."""

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
