"""Inference domain types (Phase 3)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import (
    InferenceErrorCode,
    InferenceLifecycleState,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.stage import PlaceholderStageResult


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Generation parameters for inference."""

    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class GenerationMetadata:
    """Metadata describing a generation call."""

    model_identifier: str
    adapter_type: str
    seed: int | None
    max_tokens: int
    temperature: float
    runtime: str
    extra: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Structured output from a single generation call."""

    generated_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    memory_usage_mb: float | None
    metadata: GenerationMetadata


@dataclass(frozen=True, slots=True)
class InferenceSession:
    """Immutable inference session established after successful initialization."""

    run_id: str
    bundle_digest: str
    lifecycle_state: InferenceLifecycleState
    model_identifier: str
    adapter_type: str
    runtime: str
    ready: bool = True


@dataclass(frozen=True)
class InferenceError(Exception):
    """Structured inference error."""

    code: InferenceErrorCode
    message: str
    field: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class InferenceInitializationOutcome:
    """Result of the inference initialization stage."""

    success: bool
    message: str
    session: InferenceSession | None = None
    errors: tuple[InferenceError, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_stage_result(self) -> PlaceholderStageResult:
        status = StageStatus.SUCCEEDED if self.success else StageStatus.FAILED
        data: dict[str, object] = {
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }
        if self.session is not None:
            data["bundle_digest"] = self.session.bundle_digest
            data["lifecycle_state"] = self.session.lifecycle_state.value
            data["runtime"] = self.session.runtime
        if self.errors:
            data["errors"] = tuple(
                {"code": error.code.value, "message": error.message, "field": error.field}
                for error in self.errors
            )
        return PlaceholderStageResult(
            stage=ValidationStage.INITIALIZE_INFERENCE,
            status=status,
            message=self.message,
            data=data,
        )


@dataclass(frozen=True, slots=True)
class InferenceGenerationOutcome:
    """Result of an on-demand generation call."""

    success: bool
    message: str
    result: InferenceResult | None = None
    errors: tuple[InferenceError, ...] = ()
