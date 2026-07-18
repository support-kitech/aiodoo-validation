"""Certification engine domain types (Phase 8)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.benchmark import BenchmarkExecutionResult, BenchmarkResult
from aiodoo_validation.domain.enums import (
    CertificationErrorCode,
    ExecutionTier,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.scoring import ScoreExecutionResult
from aiodoo_validation.domain.stage import PlaceholderStageResult


@dataclass(frozen=True, slots=True)
class CertificationCapability:
    """Declared capability flags for a certification policy."""

    placeholder: bool = True
    consumes_benchmark_result: bool = True
    inspects_filesystem: bool = False
    applies_thresholds: bool = False


@dataclass(frozen=True, slots=True)
class CertificationMetadata:
    """Immutable metadata describing a registered certification policy."""

    policy_id: str
    name: str
    description: str
    version: str
    supported_profile: str
    source_benchmark_policy_id: str
    capabilities: CertificationCapability


@dataclass(frozen=True)
class CertificationError(Exception):
    """Structured certification engine error."""

    code: CertificationErrorCode
    message: str
    field: str | None = None
    policy_id: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class CertificationResult:
    """Immutable result from a single certification policy."""

    policy_id: str
    source_benchmark_policy_id: str
    success: bool
    certified: bool
    certification_score: float
    certification_level: str
    message: str
    warnings: tuple[str, ...] = ()
    errors: tuple[CertificationError, ...] = ()
    duration_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class CertificationExecutionResult:
    """Immutable aggregate result of executing the certification pipeline."""

    plan_digest: str
    profile_name: str
    results: tuple[CertificationResult, ...]
    duration_ms: int
    policy_count: int
    success_count: int
    failure_count: int
    certified_count: int
    overall_certified: bool | None = None
    aggregate_certification_score: float | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[CertificationError, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class CertificationContext:
    """Immutable per-invocation context passed to certification policies."""

    run_id: str
    profile_name: str
    plan_digest: str
    protocol_major: int
    protocol_minor: int
    execution_tier: ExecutionTier
    benchmark_result: BenchmarkResult
    benchmark_execution: BenchmarkExecutionResult
    score_execution: ScoreExecutionResult | None = None
    configuration: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class CertificationExecutionOutcome:
    """Result of the CERTIFICATION stage."""

    success: bool
    message: str
    execution: CertificationExecutionResult | None = None
    errors: tuple[CertificationError, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_stage_result(self) -> PlaceholderStageResult:
        status = StageStatus.SUCCEEDED if self.success else StageStatus.FAILED
        data: dict[str, object] = {
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }
        if self.execution is not None:
            data["plan_digest"] = self.execution.plan_digest
            data["profile_name"] = self.execution.profile_name
            data["policy_count"] = self.execution.policy_count
            data["success_count"] = self.execution.success_count
            data["failure_count"] = self.execution.failure_count
            data["certified_count"] = self.execution.certified_count
            data["overall_certified"] = self.execution.overall_certified
            data["duration_ms"] = self.execution.duration_ms
            data["aggregate_certification_score"] = self.execution.aggregate_certification_score
            data["policy_ids"] = tuple(result.policy_id for result in self.execution.results)
        if self.errors:
            data["errors"] = tuple(
                {
                    "code": error.code.value,
                    "message": error.message,
                    "field": error.field,
                    "policy_id": error.policy_id,
                }
                for error in self.errors
            )
        return PlaceholderStageResult(
            stage=ValidationStage.CERTIFICATION,
            status=status,
            message=self.message,
            data=data,
        )
