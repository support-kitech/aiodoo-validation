"""Benchmark policy protocol."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.benchmark import (
    BenchmarkContext,
    BenchmarkMetadata,
    BenchmarkResult,
)


class BenchmarkPolicy(Protocol):
    """
    Contract for a benchmark policy.

    Policies consume ScoreResult values only — never inspect source files or
    re-run scoring/validation.
    """

    @property
    def metadata(self) -> BenchmarkMetadata: ...

    def benchmark(self, context: BenchmarkContext) -> BenchmarkResult: ...
