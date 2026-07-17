"""Certification policy protocol."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.certification import (
    CertificationContext,
    CertificationMetadata,
    CertificationResult,
)


class CertificationPolicy(Protocol):
    """
    Contract for a certification policy.

    Policies consume BenchmarkResult values only — never inspect source files or
    re-run validation, scoring, or benchmarking.
    """

    @property
    def metadata(self) -> CertificationMetadata: ...

    def certify(self, context: CertificationContext) -> CertificationResult: ...
