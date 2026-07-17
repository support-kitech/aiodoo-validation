"""Scoring engine port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.scoring import ScoreExecutionOutcome


class ScoringEnginePort(Protocol):
    """Consume OracleExecutionResult and produce scoring outcomes (Phase 6+)."""

    def score(self, context: RunContext) -> ScoreExecutionOutcome: ...
