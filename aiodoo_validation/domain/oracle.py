"""Oracle framework domain types (Phase 5)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import (
    ExecutionTier,
    OracleErrorCode,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.inference import InferenceSession
from aiodoo_validation.domain.stage import PlaceholderStageResult


@dataclass(frozen=True, slots=True)
class OracleCapability:
    """Declared capability flags for an oracle implementation."""

    placeholder: bool = True
    reads_artifacts: bool = False
    uses_inference: bool = False


@dataclass(frozen=True, slots=True)
class OracleMetadata:
    """Immutable metadata describing a registered oracle."""

    oracle_id: str
    name: str
    description: str
    version: str
    supported_profile: str
    capabilities: OracleCapability


@dataclass(frozen=True)
class OracleError(Exception):
    """Structured oracle framework error."""

    code: OracleErrorCode
    message: str
    field: str | None = None
    oracle_id: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class OracleResult:
    """Immutable result from a single oracle execution."""

    oracle_id: str
    success: bool
    message: str
    findings: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[OracleError, ...] = ()
    duration_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class OracleExecutionResult:
    """Immutable aggregate result of executing a ValidationPlan oracle pipeline."""

    plan_digest: str
    profile_name: str
    results: tuple[OracleResult, ...]
    duration_ms: int
    oracle_count: int
    success_count: int
    failure_count: int
    warnings: tuple[str, ...] = ()
    errors: tuple[OracleError, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class OracleContext:
    """Immutable per-invocation context passed to oracle implementations."""

    run_id: str
    profile_name: str
    plan_digest: str
    protocol_major: int
    protocol_minor: int
    execution_tier: ExecutionTier
    configuration: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    artifact_bundle: ArtifactBundle | None = None
    inference_session: InferenceSession | None = None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class OracleExecutionOutcome:
    """Result of the RUN_VALIDATION (oracle) stage."""

    success: bool
    message: str
    execution: OracleExecutionResult | None = None
    errors: tuple[OracleError, ...] = ()
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
            data["oracle_count"] = self.execution.oracle_count
            data["success_count"] = self.execution.success_count
            data["failure_count"] = self.execution.failure_count
            data["duration_ms"] = self.execution.duration_ms
            data["oracle_ids"] = tuple(result.oracle_id for result in self.execution.results)
        if self.errors:
            data["errors"] = tuple(
                {
                    "code": error.code.value,
                    "message": error.message,
                    "field": error.field,
                    "oracle_id": error.oracle_id,
                }
                for error in self.errors
            )
        return PlaceholderStageResult(
            stage=ValidationStage.RUN_VALIDATION,
            status=status,
            message=self.message,
            data=data,
        )
