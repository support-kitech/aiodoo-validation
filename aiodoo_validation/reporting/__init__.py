"""Report Generator package (Phase 9)."""

from aiodoo_validation.reporting.base import ReportTemplate
from aiodoo_validation.reporting.engine import ReportGenerator
from aiodoo_validation.reporting.registry import ReportRegistry
from aiodoo_validation.reporting.templates import (
    ManifestReportTemplate,
    MetadataReportTemplate,
    ModuleStructureReportTemplate,
    PlaceholderReportTemplate,
    PythonReportTemplate,
    QualityReportTemplate,
    SecurityReportTemplate,
    XmlReportTemplate,
)

__all__ = [
    "ManifestReportTemplate",
    "MetadataReportTemplate",
    "ModuleStructureReportTemplate",
    "PlaceholderReportTemplate",
    "PythonReportTemplate",
    "QualityReportTemplate",
    "ReportGenerator",
    "ReportRegistry",
    "ReportTemplate",
    "SecurityReportTemplate",
    "XmlReportTemplate",
]
