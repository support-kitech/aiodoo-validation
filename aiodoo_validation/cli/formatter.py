"""Human-readable console formatter (Phase 10)."""

from __future__ import annotations

from aiodoo_validation.api.metadata import PIPELINE_STAGE_ORDER_PUBLIC
from aiodoo_validation.domain.enums import ExitStatus, StageStatus, ValidationStage
from aiodoo_validation.domain.result import ValidationRunResult
from aiodoo_validation.execution import certification_label


class ConsoleFormatter:
    """Format ``ValidationRunResult`` for terminal output."""

    def format(self, result: ValidationRunResult) -> str:
        """Produce a multi-section human-readable summary."""
        lines: list[str] = []
        context = result.run_context
        duration_ms = int((result.completed_at - context.started_at).total_seconds() * 1000)

        lines.append("AIODOO Validation")
        lines.append(f"Run ID: {context.run_id}")
        lines.append(f"Exit status: {self._format_exit_label(result)}")
        lines.append(f"Duration: {duration_ms} ms")
        lines.append("")

        lines.append("Pipeline stages:")
        records_by_stage = {record.stage: record for record in context.stage_records}
        for stage in PIPELINE_STAGE_ORDER_PUBLIC:
            record = records_by_stage.get(stage)
            if record is None:
                status = StageStatus.PENDING.value
                message = ""
            else:
                status = record.status.value
                message = record.message
            suffix = f" — {message}" if message else ""
            lines.append(f"  {stage.value}: {status}{suffix}")
        lines.append("")

        if context.warnings:
            lines.append("Warnings:")
            for warning in context.warnings:
                lines.append(f"  - {warning}")
            lines.append("")

        if context.errors:
            lines.append("Errors:")
            for error in context.errors:
                lines.append(f"  - {error}")
            lines.append("")

        report_execution = context.report_execution
        if report_execution is not None:
            lines.append("Report summary:")
            lines.append(f"  Templates: {report_execution.template_count}")
            lines.append(f"  Successes: {report_execution.success_count}")
            lines.append(f"  Failures: {report_execution.failure_count}")
            if report_execution.overall_status is not None:
                lines.append(f"  Overall status: {report_execution.overall_status}")
            for report in report_execution.results:
                lines.append(f"  - {report.template_id}: {report.status} ({report.summary})")
            lines.append("")

        lines.append(result.message)
        return "\n".join(lines).rstrip() + "\n"

    def _format_exit_label(self, result: ValidationRunResult) -> str:
        """Profile-driven certification label for successful certification exits."""
        status = result.exit_status
        profile = result.run_context.request.profile_name
        if status is ExitStatus.COMPLETED:
            return certification_label(profile_name=profile, certified=True)
        if status is ExitStatus.NOT_CERTIFIED:
            return certification_label(profile_name=profile, certified=False)
        return status.value

    def format_error(self, message: str) -> str:
        return f"Error: {message}\n"

    def format_version(
        self,
        *,
        repository_version: str,
        protocol_major: int,
        protocol_minor: int,
        supported_profiles: tuple[str, ...],
        supported_execution_tiers: tuple[str, ...],
    ) -> str:
        lines = [
            "AIODOO Validation",
            f"Repository version: {repository_version}",
            f"Protocol version: {protocol_major}.{protocol_minor}",
            "Supported profiles:",
        ]
        lines.extend(f"  - {profile}" for profile in supported_profiles)
        lines.append("Supported execution tiers:")
        lines.extend(f"  - {tier}" for tier in supported_execution_tiers)
        return "\n".join(lines) + "\n"

    def format_capabilities(
        self,
        *,
        supported_profiles: tuple[str, ...],
        pipeline_stages: tuple[ValidationStage, ...],
        capabilities: tuple[str, ...],
        supported_runtimes: tuple[str, ...],
        supported_artifact_types: tuple[str, ...],
    ) -> str:
        lines = [
            "AIODOO Validation Capabilities",
            "Supported profiles:",
        ]
        lines.extend(f"  - {profile}" for profile in supported_profiles)
        lines.append("Pipeline stages:")
        lines.extend(f"  - {stage.value}" for stage in pipeline_stages)
        lines.append("Profile capabilities:")
        lines.extend(f"  - {capability}" for capability in capabilities)
        lines.append("Supported runtimes:")
        lines.extend(f"  - {runtime}" for runtime in supported_runtimes)
        lines.append("Supported artifact types:")
        lines.extend(f"  - {artifact_type}" for artifact_type in supported_artifact_types)
        return "\n".join(lines) + "\n"

    def format_help(self, *, program_name: str, usage: str, examples: tuple[str, ...]) -> str:
        lines = [
            "AIODOO Validation CLI",
            "",
            "Usage:",
            usage,
            "",
            "Commands:",
            f"  {program_name} validate   Run a validation lifecycle",
            f"  {program_name} version     Show version and protocol metadata",
            f"  {program_name} capabilities Show supported profiles and pipeline metadata",
            f"  {program_name} help        Show this help message",
            "",
            "Examples:",
        ]
        lines.extend(f"  {example}" for example in examples)
        return "\n".join(lines) + "\n"
