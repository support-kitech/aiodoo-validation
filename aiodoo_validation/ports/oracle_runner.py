"""Oracle runner port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.oracle import OracleExecutionOutcome


class OracleRunnerPort(Protocol):
    """Execute ValidationPlan oracle pipeline (Phase 5+)."""

    def execute_oracles(self, context: RunContext) -> OracleExecutionOutcome: ...
