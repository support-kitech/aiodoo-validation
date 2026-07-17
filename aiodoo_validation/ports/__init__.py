"""Port interfaces for validation pipeline collaborators."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.stage import PlaceholderStageResult
from aiodoo_validation.ports.artifact_resolver import ArtifactResolverPort
from aiodoo_validation.ports.benchmark_engine import BenchmarkEnginePort
from aiodoo_validation.ports.certification_engine import CertificationEnginePort
from aiodoo_validation.ports.inference_runner import InferenceRunnerPort
from aiodoo_validation.ports.oracle_runner import OracleRunnerPort
from aiodoo_validation.ports.profile_engine import ProfileEnginePort
from aiodoo_validation.ports.report_generator import ReportGeneratorPort
from aiodoo_validation.ports.scoring_engine import ScoringEnginePort

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
