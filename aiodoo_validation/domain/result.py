"""Validation run result."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ExitStatus


@dataclass(frozen=True, slots=True)
class ValidationRunResult:
    """Final outcome of a validation engine run."""

    exit_status: ExitStatus
    run_context: RunContext
    message: str
    completed_at: datetime
