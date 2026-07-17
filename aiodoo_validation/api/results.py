"""ValidationRunResult helpers for ecosystem consumers (Phase 11)."""

from __future__ import annotations

from aiodoo_validation.domain.enums import ExitStatus, StageStatus, ValidationStage
from aiodoo_validation.domain.report import ReportExecutionResult
from aiodoo_validation.domain.result import ValidationRunResult
from aiodoo_validation.engine import PIPELINE_STAGE_ORDER


def is_successful(result: ValidationRunResult) -> bool:
    """Return whether the validation lifecycle completed without failure."""
    return result.exit_status not in {
        ExitStatus.FAILED,
        ExitStatus.INVALID_REQUEST,
        ExitStatus.INTERNAL_ERROR,
    }


def is_certified(result: ValidationRunResult) -> bool:
    """Return whether the run reached a certified exit status."""
    return result.exit_status is ExitStatus.COMPLETED


def report_execution(result: ValidationRunResult) -> ReportExecutionResult | None:
    """Return report execution metadata when available."""
    return result.run_context.report_execution


def stage_statuses(result: ValidationRunResult) -> dict[ValidationStage, StageStatus]:
    """Return the latest status for each executed pipeline stage."""
    statuses: dict[ValidationStage, StageStatus] = {}
    for record in result.run_context.stage_records:
        statuses[record.stage] = record.status
    for stage in PIPELINE_STAGE_ORDER:
        statuses.setdefault(stage, StageStatus.PENDING)
    return statuses
