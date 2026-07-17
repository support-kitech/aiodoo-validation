"""Certification engine port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.certification import CertificationExecutionOutcome
from aiodoo_validation.domain.context import RunContext


class CertificationEnginePort(Protocol):
    """Consume BenchmarkExecutionResult and produce certification outcomes (Phase 8+)."""

    def certify(self, context: RunContext) -> CertificationExecutionOutcome: ...
