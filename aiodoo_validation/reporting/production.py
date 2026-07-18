"""Production report templates — summarize real certification outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.report import (
    ReportCapability,
    ReportContext,
    ReportMetadata,
    ReportResult,
    ReportSection,
)


def _metadata(
    *,
    template_id: str,
    name: str,
    source_certification_policy_id: str,
    supported_profile: str,
) -> ReportMetadata:
    return ReportMetadata(
        template_id=template_id,
        name=name,
        description=f"Production report for {source_certification_policy_id}.",
        version="1.0.0",
        supported_profile=supported_profile,
        source_certification_policy_id=source_certification_policy_id,
        capabilities=ReportCapability(
            placeholder=False,
            consumes_certification_result=True,
            inspects_filesystem=False,
            renders_output=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class CertificationSummaryReportTemplate:
    """Emit a real report object from a CertificationResult."""

    metadata: ReportMetadata

    def generate(self, context: ReportContext) -> ReportResult:
        started = perf_counter()
        cert = context.certification_result
        if cert.success and cert.certified:
            status = "SUCCESS"
        elif cert.success:
            status = "NOT_CERTIFIED"
        else:
            status = "FAIL"
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        section = ReportSection(
            section_id=f"{self.metadata.template_id}.summary",
            title=self.metadata.name,
            content=(cert.message,),
        )
        return ReportResult(
            template_id=self.metadata.template_id,
            source_certification_policy_id=self.metadata.source_certification_policy_id,
            success=True,
            status=status,
            summary=cert.message,
            sections=(section,),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "certified": cert.certified,
                    "certification_level": cert.certification_level,
                    "certification_score": cert.certification_score,
                    "plan_digest": context.plan_digest,
                }
            ),
        )


def default_production_report_templates(
    *,
    profile: str = "coding",
) -> tuple[CertificationSummaryReportTemplate, ...]:
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    return tuple(
        CertificationSummaryReportTemplate(
            metadata=_metadata(
                template_id=f"{profile}.report.{name}",
                name=f"{name.replace('_', ' ').title()} Report",
                source_certification_policy_id=f"{profile}.certification.{name}",
                supported_profile=profile,
            )
        )
        for name in names
    )


def default_production_coding_report_templates(
    *,
    supported_profile: str = "coding",
) -> tuple[CertificationSummaryReportTemplate, ...]:
    return default_production_report_templates(profile=supported_profile)


__all__ = [
    "CertificationSummaryReportTemplate",
    "default_production_report_templates",
    "default_production_coding_report_templates",
]
