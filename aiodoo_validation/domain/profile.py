"""Profile resolution domain types (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.enums import ProfileErrorCode, StageStatus, ValidationStage
from aiodoo_validation.domain.stage import PlaceholderStageResult
from aiodoo_validation.validation_plan import ValidationPlan


@dataclass(frozen=True)
class ProfileError(Exception):
    """Structured profile resolution error."""

    code: ProfileErrorCode
    message: str
    field: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class ResolvedProfile:
    """Base immutable resolved profile attached to RunContext."""

    profile_name: str


@dataclass(frozen=True, slots=True)
class ProfileResolutionOutcome:
    """Result of the profile resolution stage."""

    success: bool
    message: str
    profile: ResolvedProfile | None = None
    plan: ValidationPlan | None = None
    errors: tuple[ProfileError, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_stage_result(self) -> PlaceholderStageResult:
        status = StageStatus.SUCCEEDED if self.success else StageStatus.FAILED
        data: dict[str, object] = {
            "success": self.success,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }
        if self.profile is not None:
            data["profile_name"] = self.profile.profile_name
        if self.plan is not None:
            data["plan_digest"] = self.plan.plan_digest
        if self.errors:
            data["errors"] = tuple(
                {"code": error.code.value, "message": error.message, "field": error.field}
                for error in self.errors
            )
        return PlaceholderStageResult(
            stage=ValidationStage.RESOLVE_PROFILE,
            status=status,
            message=self.message,
            data=data,
        )
