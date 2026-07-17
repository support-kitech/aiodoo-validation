"""Benchmark engine domain types (Phase 7)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import (
    BenchmarkErrorCode,
    ExecutionTier,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.scoring import ScoreExecutionResult, ScoreResult
from aiodoo_validation.domain.stage import PlaceholderStageResult


@dataclass(frozen=True, slots=True)
class BenchmarkCapability:
    """Declared capability flags for a benchmark policy."""

    placeholder: bool = True
    consumes_score_result: bool = True
    inspects_filesystem: bool = False
    uses_datasets: bool = False


@dataclass(frozen=True, slots=True)
class BenchmarkMetadata:
    """Immutable metadata describing a registered benchmark policy."""

    policy_id: str
    name: str
    description: str
    version: str
    supported_profile: str
    source_score_policy_id: str
    capabilities: BenchmarkCapability


@dataclass(frozen=True)
class BenchmarkError(Exception):
    """Structured benchmark engine error."""

    code: BenchmarkErrorCode
    message: str
    field: str | None = None
    policy_id: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Immutable result from a single benchmark policy."""

    policy_id: str
    source_score_policy_id: str
    success: bool
    benchmark_score: float
    benchmark_pass: bool
    benchmark_rank: int
    message: str
    warnings: tuple[str, ...] = ()
    errors: tuple[BenchmarkError, ...] = ()
    duration_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class BenchmarkExecutionResult:
    """Immutable aggregate result of executing the benchmark pipeline."""

    plan_digest: str
    profile_name: str
    results: tuple[BenchmarkResult, ...]
    duration_ms: int
    policy_count: int
    success_count: int
    failure_count: int
    aggregate_benchmark_score: float | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[BenchmarkError, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class BenchmarkContext:
    """Immutable per-invocation context passed to benchmark policies."""

    run_id: str
    profile_name: str
    plan_digest: str
    protocol_major: int
    protocol_minor: int
    execution_tier: ExecutionTier
    score_result: ScoreResult
    score_execution: ScoreExecutionResult
    configuration: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class BenchmarkExecutionOutcome:
    """Result of the BENCHMARK stage."""

    success: bool
    message: str
    execution: BenchmarkExecutionResult | None = None
    errors: tuple[BenchmarkError, ...] = ()
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
            data["duration_ms"] = self.execution.duration_ms
            data["aggregate_benchmark_score"] = self.execution.aggregate_benchmark_score
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
            stage=ValidationStage.BENCHMARK,
            status=status,
            message=self.message,
            data=data,
        )
