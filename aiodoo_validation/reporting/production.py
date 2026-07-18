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
from aiodoo_validation.execution import certification_label


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
        version="1.1.0",
        supported_profile=supported_profile,
        source_certification_policy_id=source_certification_policy_id,
        capabilities=ReportCapability(
            placeholder=False,
            consumes_certification_result=True,
            inspects_filesystem=False,
            renders_output=False,
        ),
    )


def _section(section_id: str, title: str, lines: tuple[str, ...]) -> ReportSection:
    return ReportSection(section_id=section_id, title=title, content=lines)


@dataclass(frozen=True, slots=True)
class CertificationSummaryReportTemplate:
    """Emit a rich, machine-readable report object from run + certification data."""

    metadata: ReportMetadata

    def generate(self, context: ReportContext) -> ReportResult:
        started = perf_counter()
        cert = context.certification_result
        summary_map = dict(context.run_summary)
        label = certification_label(
            profile_name=context.profile_name,
            certified=bool(cert.certified),
        )
        if cert.success and cert.certified:
            status = "SUCCESS"
        elif cert.success:
            status = "NOT_CERTIFIED"
        else:
            status = "FAIL"

        reasons = cert.metadata.get("criteria_reasons") or ()
        if isinstance(reasons, tuple):
            reason_lines = tuple(str(item) for item in reasons)
        elif isinstance(reasons, list):
            reason_lines = tuple(str(item) for item in reasons)
        else:
            reason_lines = (str(reasons),) if reasons else ()

        structural = summary_map.get("structural_validation") or {}
        behavior = summary_map.get("behavior_validation") or {}
        score_summary = summary_map.get("score_summary") or {}
        bench_summary = summary_map.get("benchmark_summary") or {}
        cert_decision = summary_map.get("certification_decision") or {}
        timing = summary_map.get("timing_ms") or {}
        artifacts = summary_map.get("artifacts") or {}
        warnings = summary_map.get("warnings") or ()

        sections = (
            _section(
                f"{self.metadata.template_id}.overview",
                "Overview",
                (
                    f"profile={context.profile_name}",
                    f"execution_tier={context.execution_tier.value}",
                    f"plan_digest={context.plan_digest}",
                    f"certification_label={label}",
                    f"decision={cert.message}",
                ),
            ),
            _section(
                f"{self.metadata.template_id}.structural",
                "Structural Validation",
                (
                    f"oracle_ids={structural.get('oracle_ids', ())}",
                    f"success_count={structural.get('success_count')}",
                    f"failure_count={structural.get('failure_count')}",
                ),
            ),
            _section(
                f"{self.metadata.template_id}.behavior",
                "Behavior Validation",
                (
                    f"status={behavior.get('status', 'deferred')}",
                    f"enabled={behavior.get('enabled', False)}",
                    f"oracle_ids={behavior.get('oracle_ids', ())}",
                ),
            ),
            _section(
                f"{self.metadata.template_id}.scores",
                "Score Summary",
                (
                    f"policy_count={score_summary.get('policy_count')}",
                    f"aggregate_score={score_summary.get('aggregate_score')}",
                    f"success_count={score_summary.get('success_count')}",
                ),
            ),
            _section(
                f"{self.metadata.template_id}.benchmark",
                "Benchmark Summary",
                (
                    f"policy_count={bench_summary.get('policy_count')}",
                    f"aggregate_benchmark_score={bench_summary.get('aggregate_benchmark_score')}",
                    f"success_count={bench_summary.get('success_count')}",
                ),
            ),
            _section(
                f"{self.metadata.template_id}.certification",
                "Certification Decision",
                (
                    f"label={label}",
                    f"overall_certified={cert_decision.get('overall_certified')}",
                    f"certified={cert.certified}",
                    f"level={cert.certification_level}",
                    f"score={cert.certification_score}",
                    *(f"reason={reason}" for reason in reason_lines),
                ),
            ),
            _section(
                f"{self.metadata.template_id}.timing",
                "Timing",
                tuple(f"{key}={value}" for key, value in timing.items()),
            ),
            _section(
                f"{self.metadata.template_id}.artifacts",
                "Artifacts Validated",
                tuple(f"{key}={value}" for key, value in artifacts.items()),
            ),
            _section(
                f"{self.metadata.template_id}.warnings",
                "Warnings",
                tuple(str(item) for item in warnings) or ("none",),
            ),
        )
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return ReportResult(
            template_id=self.metadata.template_id,
            source_certification_policy_id=self.metadata.source_certification_policy_id,
            success=True,
            status=status,
            summary=f"{label}: {cert.message}",
            sections=sections,
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "certified": cert.certified,
                    "certification_label": label,
                    "certification_level": cert.certification_level,
                    "certification_score": cert.certification_score,
                    "plan_digest": context.plan_digest,
                    "execution_tier": context.execution_tier.value,
                    "profile": context.profile_name,
                    "run_summary": summary_map,
                    "machine_readable": True,
                }
            ),
        )


def default_production_report_templates(
    *,
    profile: str = "coding",
) -> tuple[CertificationSummaryReportTemplate, ...]:
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    templates: list[CertificationSummaryReportTemplate] = [
        CertificationSummaryReportTemplate(
            metadata=_metadata(
                template_id=f"{profile}.report.{name}",
                name=f"{name.replace('_', ' ').title()} Report",
                source_certification_policy_id=f"{profile}.certification.{name}",
                supported_profile=profile,
            )
        )
        for name in names
    ]
    if profile == "repair":
        templates.append(
            CertificationSummaryReportTemplate(
                metadata=_metadata(
                    template_id="repair.report.behavior",
                    name="Repair Behavior Report",
                    source_certification_policy_id="repair.certification.behavior",
                    supported_profile="repair",
                )
            )
        )
    if profile == "coding":
        templates.append(
            CertificationSummaryReportTemplate(
                metadata=_metadata(
                    template_id="coding.report.behavior",
                    name="Coding Behavior Report",
                    source_certification_policy_id="coding.certification.behavior",
                    supported_profile="coding",
                )
            )
        )
    return tuple(templates)


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
