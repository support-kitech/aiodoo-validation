"""Report generator domain types (Phase 9)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.certification import (
    CertificationExecutionResult,
    CertificationResult,
)
from aiodoo_validation.domain.enums import (
    ExecutionTier,
    ReportErrorCode,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.stage import PlaceholderStageResult


@dataclass(frozen=True, slots=True)
class ReportCapability:
    """Declared capability flags for a report template."""

    placeholder: bool = True
    consumes_certification_result: bool = True
    inspects_filesystem: bool = False
    renders_output: bool = False


@dataclass(frozen=True, slots=True)
class ReportMetadata:
    """Immutable metadata describing a registered report template."""

    template_id: str
    name: str
    description: str
    version: str
    supported_profile: str
    source_certification_policy_id: str
    capabilities: ReportCapability


@dataclass(frozen=True)
class ReportError(Exception):
    """Structured report generator error."""

    code: ReportErrorCode
    message: str
    field: str | None = None
    template_id: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class ReportSection:
    """Immutable section within a single report result."""

    section_id: str
    title: str
    content: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReportResult:
    """Immutable result from a single report template."""

    template_id: str
    source_certification_policy_id: str
    success: bool
    status: str
    summary: str
    sections: tuple[ReportSection, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[ReportError, ...] = ()
    duration_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ReportExecutionResult:
    """Immutable aggregate result of executing the report pipeline."""

    plan_digest: str
    profile_name: str
    results: tuple[ReportResult, ...]
    duration_ms: int
    template_count: int
    success_count: int
    failure_count: int
    overall_status: str | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[ReportError, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ReportContext:
    """Immutable per-invocation context passed to report templates."""

    run_id: str
    profile_name: str
    plan_digest: str
    protocol_major: int
    protocol_minor: int
    execution_tier: ExecutionTier
    certification_result: CertificationResult
    certification_execution: CertificationExecutionResult
    configuration: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ReportExecutionOutcome:
    """Result of the REPORT stage."""

    success: bool
    message: str
    execution: ReportExecutionResult | None = None
    errors: tuple[ReportError, ...] = ()
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
            data["template_count"] = self.execution.template_count
            data["success_count"] = self.execution.success_count
            data["failure_count"] = self.execution.failure_count
            data["overall_status"] = self.execution.overall_status
            data["duration_ms"] = self.execution.duration_ms
            data["template_ids"] = tuple(result.template_id for result in self.execution.results)
        if self.errors:
            data["errors"] = tuple(
                {
                    "code": error.code.value,
                    "message": error.message,
                    "field": error.field,
                    "template_id": error.template_id,
                }
                for error in self.errors
            )
        return PlaceholderStageResult(
            stage=ValidationStage.REPORT,
            status=status,
            message=self.message,
            data=data,
        )
