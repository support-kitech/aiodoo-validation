"""Placeholder report templates (Phase 9 — no rendering or export)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_MANIFEST,
    CODING_CERTIFICATION_METADATA,
    CODING_CERTIFICATION_MODULE_STRUCTURE,
    CODING_CERTIFICATION_PYTHON,
    CODING_CERTIFICATION_QUALITY,
    CODING_CERTIFICATION_SECURITY,
    CODING_CERTIFICATION_XML,
)
from aiodoo_validation.domain.report import (
    ReportCapability,
    ReportContext,
    ReportMetadata,
    ReportResult,
    ReportSection,
)
from aiodoo_validation.reporting.ids import (
    CODING_REPORT_MANIFEST,
    CODING_REPORT_METADATA,
    CODING_REPORT_MODULE_STRUCTURE,
    CODING_REPORT_PYTHON,
    CODING_REPORT_QUALITY,
    CODING_REPORT_SECURITY,
    CODING_REPORT_XML,
    PLACEHOLDER_REPORT_STATUS,
    PLACEHOLDER_REPORT_SUMMARY,
)


def placeholder_report_metadata(
    *,
    template_id: str,
    name: str,
    description: str,
    source_certification_policy_id: str,
    supported_profile: str = "coding",
    version: str = "0.0.0-placeholder",
) -> ReportMetadata:
    return ReportMetadata(
        template_id=template_id,
        name=name,
        description=description,
        version=version,
        supported_profile=supported_profile,
        source_certification_policy_id=source_certification_policy_id,
        capabilities=ReportCapability(
            placeholder=True,
            consumes_certification_result=True,
            inspects_filesystem=False,
            renders_output=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class PlaceholderReportTemplate:
    """Base placeholder template returning deterministic report objects."""

    metadata: ReportMetadata

    def generate(self, context: ReportContext) -> ReportResult:
        started = perf_counter()
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return ReportResult(
            template_id=self.metadata.template_id,
            source_certification_policy_id=self.metadata.source_certification_policy_id,
            success=True,
            status=PLACEHOLDER_REPORT_STATUS,
            summary=PLACEHOLDER_REPORT_SUMMARY,
            sections=(
                ReportSection(
                    section_id=f"{self.metadata.template_id}.summary",
                    title="Summary",
                    content=(PLACEHOLDER_REPORT_SUMMARY,),
                ),
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": True,
                    "certified": context.certification_result.certified,
                    "certification_score": context.certification_result.certification_score,
                    "plan_digest": context.plan_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class MetadataReportTemplate(PlaceholderReportTemplate):
    @staticmethod
    def create() -> MetadataReportTemplate:
        return MetadataReportTemplate(
            metadata=placeholder_report_metadata(
                template_id=CODING_REPORT_METADATA,
                name="Metadata Report Template",
                description="Placeholder metadata report template.",
                source_certification_policy_id=CODING_CERTIFICATION_METADATA,
            )
        )


@dataclass(frozen=True, slots=True)
class ManifestReportTemplate(PlaceholderReportTemplate):
    @staticmethod
    def create() -> ManifestReportTemplate:
        return ManifestReportTemplate(
            metadata=placeholder_report_metadata(
                template_id=CODING_REPORT_MANIFEST,
                name="Manifest Report Template",
                description="Placeholder manifest report template.",
                source_certification_policy_id=CODING_CERTIFICATION_MANIFEST,
            )
        )


@dataclass(frozen=True, slots=True)
class PythonReportTemplate(PlaceholderReportTemplate):
    @staticmethod
    def create() -> PythonReportTemplate:
        return PythonReportTemplate(
            metadata=placeholder_report_metadata(
                template_id=CODING_REPORT_PYTHON,
                name="Python Report Template",
                description="Placeholder Python report template.",
                source_certification_policy_id=CODING_CERTIFICATION_PYTHON,
            )
        )


@dataclass(frozen=True, slots=True)
class XmlReportTemplate(PlaceholderReportTemplate):
    @staticmethod
    def create() -> XmlReportTemplate:
        return XmlReportTemplate(
            metadata=placeholder_report_metadata(
                template_id=CODING_REPORT_XML,
                name="XML Report Template",
                description="Placeholder XML report template.",
                source_certification_policy_id=CODING_CERTIFICATION_XML,
            )
        )


@dataclass(frozen=True, slots=True)
class SecurityReportTemplate(PlaceholderReportTemplate):
    @staticmethod
    def create() -> SecurityReportTemplate:
        return SecurityReportTemplate(
            metadata=placeholder_report_metadata(
                template_id=CODING_REPORT_SECURITY,
                name="Security Report Template",
                description="Placeholder security report template.",
                source_certification_policy_id=CODING_CERTIFICATION_SECURITY,
            )
        )


@dataclass(frozen=True, slots=True)
class ModuleStructureReportTemplate(PlaceholderReportTemplate):
    @staticmethod
    def create() -> ModuleStructureReportTemplate:
        return ModuleStructureReportTemplate(
            metadata=placeholder_report_metadata(
                template_id=CODING_REPORT_MODULE_STRUCTURE,
                name="Module Structure Report Template",
                description="Placeholder module structure report template.",
                source_certification_policy_id=CODING_CERTIFICATION_MODULE_STRUCTURE,
            )
        )


@dataclass(frozen=True, slots=True)
class QualityReportTemplate(PlaceholderReportTemplate):
    """Future quality report template (available for plugins; disabled in plan)."""

    @staticmethod
    def create() -> QualityReportTemplate:
        return QualityReportTemplate(
            metadata=placeholder_report_metadata(
                template_id=CODING_REPORT_QUALITY,
                name="Quality Report Template",
                description="Placeholder future quality report template.",
                source_certification_policy_id=CODING_CERTIFICATION_QUALITY,
            )
        )


def default_coding_placeholder_templates() -> tuple[PlaceholderReportTemplate, ...]:
    return (
        MetadataReportTemplate.create(),
        ManifestReportTemplate.create(),
        PythonReportTemplate.create(),
        XmlReportTemplate.create(),
        SecurityReportTemplate.create(),
        ModuleStructureReportTemplate.create(),
    )
