"""Process exit code mapping for CLI (Phase 10)."""

from __future__ import annotations

from aiodoo_validation.domain.enums import ExitStatus

EXIT_CERTIFIED = 0
EXIT_NOT_CERTIFIED = 1
EXIT_FAILED = 2
EXIT_INVALID_REQUEST = 3


def exit_code_for_status(status: ExitStatus) -> int:
    """Map ``ValidationRunResult.exit_status`` to a process exit code."""
    mapping: dict[ExitStatus, int] = {
        ExitStatus.COMPLETED: EXIT_CERTIFIED,
        ExitStatus.NOT_CERTIFIED: EXIT_NOT_CERTIFIED,
        ExitStatus.FAILED: EXIT_FAILED,
        ExitStatus.INVALID_REQUEST: EXIT_INVALID_REQUEST,
        ExitStatus.INTERNAL_ERROR: EXIT_FAILED,
    }
    return mapping[status]
