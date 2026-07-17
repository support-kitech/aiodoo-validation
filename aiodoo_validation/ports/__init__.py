"""Port interfaces for validation pipeline collaborators."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.stage import PlaceholderStageResult


class ArtifactResolverPort(Protocol):
    """Resolve base model and adapter references (Phase 2+)."""

    def resolve(self, context: RunContext) -> PlaceholderStageResult: ...


class ProfileEnginePort(Protocol):
    """Select and plan validation profile checks (Phase 4+)."""

    def resolve_profile(self, context: RunContext) -> PlaceholderStageResult: ...


class InferenceRunnerPort(Protocol):
    """Load model and run inference (Phase 3+)."""

    def initialize(self, context: RunContext) -> PlaceholderStageResult: ...


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
