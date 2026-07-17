"""Benchmark engine port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.benchmark import BenchmarkExecutionOutcome
from aiodoo_validation.domain.context import RunContext


class BenchmarkEnginePort(Protocol):
    """Consume ScoreExecutionResult and produce benchmark outcomes (Phase 7+)."""

    def benchmark(self, context: RunContext) -> BenchmarkExecutionOutcome: ...
