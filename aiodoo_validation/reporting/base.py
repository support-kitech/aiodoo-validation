"""Report template protocol."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.report import (
    ReportContext,
    ReportMetadata,
    ReportResult,
)


class ReportTemplate(Protocol):
    """
    Contract for a report template.

    Templates consume CertificationResult values only — never inspect source
    files, re-run validation, scoring, benchmarking, or certification.
    """

    @property
    def metadata(self) -> ReportMetadata: ...

    def generate(self, context: ReportContext) -> ReportResult: ...
