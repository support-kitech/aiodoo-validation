"""Artifact resolution outcome types."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import ArtifactResolutionErrorCode, StageStatus, ValidationStage
from aiodoo_validation.domain.stage import PlaceholderStageResult


@dataclass(frozen=True, slots=True)
class ArtifactResolutionError:
    """Structured artifact validation error."""

    code: ArtifactResolutionErrorCode
    message: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactResolutionOutcome:
    """Result of the artifact resolution stage."""

    success: bool
    message: str
    bundle: ArtifactBundle | None = None
    errors: tuple[ArtifactResolutionError, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_stage_result(self) -> PlaceholderStageResult:
        status = StageStatus.SUCCEEDED if self.success else StageStatus.FAILED
        data: dict[str, object] = {
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }
        if self.bundle is not None:
            data["bundle_digest"] = self.bundle.bundle_digest
        if self.errors:
            data["errors"] = tuple(
                {"code": error.code.value, "message": error.message, "field": error.field}
                for error in self.errors
            )
        return PlaceholderStageResult(
            stage=ValidationStage.RESOLVE_ARTIFACTS,
            status=status,
            message=self.message,
            data=data,
        )
