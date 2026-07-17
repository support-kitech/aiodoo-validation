"""Scoring engine domain types (Phase 6)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import (
    ExecutionTier,
    ScoreErrorCode,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.oracle import OracleExecutionResult, OracleResult
from aiodoo_validation.domain.stage import PlaceholderStageResult


@dataclass(frozen=True, slots=True)
class ScoreCapability:
    """Declared capability flags for a scoring policy."""

    placeholder: bool = True
    consumes_oracle_result: bool = True
    inspects_filesystem: bool = False


@dataclass(frozen=True, slots=True)
class ScoreMetadata:
    """Immutable metadata describing a registered scoring policy."""

    policy_id: str
    name: str
    description: str
    version: str
    supported_profile: str
    source_oracle_id: str
    capabilities: ScoreCapability


@dataclass(frozen=True)
class ScoreError(Exception):
    """Structured scoring engine error."""

    code: ScoreErrorCode
    message: str
    field: str | None = None
    policy_id: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """Immutable result from a single scoring policy."""

    policy_id: str
    source_oracle_id: str
    success: bool
    score: float
    message: str
    warnings: tuple[str, ...] = ()
    errors: tuple[ScoreError, ...] = ()
    duration_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ScoreExecutionResult:
    """Immutable aggregate result of executing the scoring pipeline."""

    plan_digest: str
    profile_name: str
    results: tuple[ScoreResult, ...]
    duration_ms: int
    policy_count: int
    success_count: int
    failure_count: int
    aggregate_score: float | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[ScoreError, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ScoreContext:
    """Immutable per-invocation context passed to scoring policies."""

    run_id: str
    profile_name: str
    plan_digest: str
    protocol_major: int
    protocol_minor: int
    execution_tier: ExecutionTier
    oracle_result: OracleResult
    oracle_execution: OracleExecutionResult
    configuration: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ScoreExecutionOutcome:
    """Result of the SCORING stage."""

    success: bool
    message: str
    execution: ScoreExecutionResult | None = None
    errors: tuple[ScoreError, ...] = ()
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
            data["aggregate_score"] = self.execution.aggregate_score
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
            stage=ValidationStage.SCORING,
            status=status,
            message=self.message,
            data=data,
        )
