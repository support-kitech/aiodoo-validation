"""Report generator port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.report import ReportExecutionOutcome


class ReportGeneratorPort(Protocol):
    """Consume CertificationExecutionResult and produce report outcomes (Phase 9+)."""

    def generate_report(self, context: RunContext) -> ReportExecutionOutcome: ...
