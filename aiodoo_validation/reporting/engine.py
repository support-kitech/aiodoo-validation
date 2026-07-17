"""Report generator engine — consume CertificationExecutionResult only (Phase 9)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.certification import CertificationExecutionResult, CertificationResult
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ReportErrorCode
from aiodoo_validation.domain.report import (
    ReportContext,
    ReportError,
    ReportExecutionOutcome,
    ReportExecutionResult,
    ReportResult,
)
from aiodoo_validation.reporting.ids import PLACEHOLDER_REPORT_STATUS
from aiodoo_validation.reporting.registry import ReportRegistry
from aiodoo_validation.validation_plan.plan import ValidationPlan


@dataclass(frozen=True, slots=True)
class ReportGenerator:
    """
    Execute registered report templates against CertificationExecutionResult.

    Never inspects XML, Python, manifests, security files, or the filesystem.
    Never re-runs validation, scoring, benchmarking, or certification. Consumes
    certification results only.
    """

    registry: ReportRegistry

    @classmethod
    def create_default(cls) -> ReportGenerator:
        return cls(registry=ReportRegistry.create_default())

    def generate_report(self, context: RunContext) -> ReportExecutionOutcome:
        try:
            return self._generate_report(context)
        except ReportError as exc:
            return ReportExecutionOutcome(
                success=False,
                message="Report generation failed.",
                errors=(exc,),
            )
        except Exception as exc:  # noqa: BLE001 — report engine must never crash callers
            return ReportExecutionOutcome(
                success=False,
                message="Report generation failed.",
                errors=(
                    ReportError(
                        code=ReportErrorCode.EXECUTION_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _generate_report(self, context: RunContext) -> ReportExecutionOutcome:
        plan = context.validation_plan
        profile = context.validation_profile
        certification_execution = context.certification_execution

        if plan is None:
            return ReportExecutionOutcome(
                success=False,
                message="Report generation failed.",
                errors=(
                    ReportError(
                        code=ReportErrorCode.MISSING_PLAN,
                        message="ValidationPlan is required before report generation.",
                        field="validation_plan",
                    ),
                ),
            )
        if profile is None:
            return ReportExecutionOutcome(
                success=False,
                message="Report generation failed.",
                errors=(
                    ReportError(
                        code=ReportErrorCode.MISSING_PROFILE,
                        message="Resolved profile is required before report generation.",
                        field="validation_profile",
                    ),
                ),
            )
        if certification_execution is None:
            return ReportExecutionOutcome(
                success=False,
                message="Report generation failed.",
                errors=(
                    ReportError(
                        code=ReportErrorCode.MISSING_CERTIFICATION_RESULTS,
                        message=(
                            "CertificationExecutionResult is required before report generation."
                        ),
                        field="certification_execution",
                    ),
                ),
            )

        if not plan.capabilities.supports_reports:
            return ReportExecutionOutcome(
                success=False,
                message="Report generation failed.",
                errors=(
                    ReportError(
                        code=ReportErrorCode.CAPABILITY_MISMATCH,
                        message=(
                            f"ValidationPlan for profile {plan.profile_name!r} "
                            "does not support reports."
                        ),
                        field="capabilities.supports_reports",
                    ),
                ),
            )

        certification_by_id = {
            result.policy_id: result for result in certification_execution.results
        }
        started = perf_counter()
        results: list[ReportResult] = []
        errors: list[ReportError] = []
        warnings: list[str] = []

        for stage in plan.report_pipeline:
            if not stage.enabled:
                continue
            try:
                template = self.registry.get(stage.stage_id)
            except ReportError as exc:
                errors.append(exc)
                results.append(
                    ReportResult(
                        template_id=stage.stage_id,
                        source_certification_policy_id="",
                        success=False,
                        status="FAIL",
                        summary=exc.message,
                        errors=(exc,),
                    )
                )
                continue

            if template.metadata.supported_profile != plan.profile_name:
                mismatch = ReportError(
                    code=ReportErrorCode.PROFILE_MISMATCH,
                    message=(
                        f"Report template supports profile "
                        f"{template.metadata.supported_profile!r} "
                        f"but plan is {plan.profile_name!r}."
                    ),
                    field="supported_profile",
                    template_id=template.metadata.template_id,
                )
                errors.append(mismatch)
                results.append(
                    ReportResult(
                        template_id=template.metadata.template_id,
                        source_certification_policy_id=(
                            template.metadata.source_certification_policy_id
                        ),
                        success=False,
                        status="FAIL",
                        summary=mismatch.message,
                        errors=(mismatch,),
                    )
                )
                continue

            certification_result = certification_by_id.get(
                template.metadata.source_certification_policy_id
            )
            if certification_result is None:
                missing = ReportError(
                    code=ReportErrorCode.CERTIFICATION_RESULT_MISSING,
                    message=(
                        f"No CertificationResult for source certification policy "
                        f"{template.metadata.source_certification_policy_id!r}."
                    ),
                    field="source_certification_policy_id",
                    template_id=template.metadata.template_id,
                )
                errors.append(missing)
                results.append(
                    ReportResult(
                        template_id=template.metadata.template_id,
                        source_certification_policy_id=(
                            template.metadata.source_certification_policy_id
                        ),
                        success=False,
                        status="FAIL",
                        summary=missing.message,
                        errors=(missing,),
                    )
                )
                continue

            report_context = self._build_report_context(
                context,
                plan=plan,
                certification_execution=certification_execution,
                certification_result=certification_result,
            )
            try:
                result = template.generate(report_context)
            except ReportError as exc:
                errors.append(exc)
                results.append(
                    ReportResult(
                        template_id=template.metadata.template_id,
                        source_certification_policy_id=(
                            template.metadata.source_certification_policy_id
                        ),
                        success=False,
                        status="FAIL",
                        summary=exc.message,
                        errors=(exc,),
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 — isolate template failures
                wrapped = ReportError(
                    code=ReportErrorCode.EXECUTION_FAILURE,
                    message=(
                        f"Report template {template.metadata.template_id!r} failed: {exc}"
                    ),
                    template_id=template.metadata.template_id,
                )
                errors.append(wrapped)
                results.append(
                    ReportResult(
                        template_id=template.metadata.template_id,
                        source_certification_policy_id=(
                            template.metadata.source_certification_policy_id
                        ),
                        success=False,
                        status="FAIL",
                        summary=wrapped.message,
                        errors=(wrapped,),
                    )
                )
                continue

            results.append(result)
            warnings.extend(result.warnings)
            if not result.success:
                errors.extend(result.errors)
                if not result.errors:
                    errors.append(
                        ReportError(
                            code=ReportErrorCode.EXECUTION_FAILURE,
                            message=result.summary,
                            template_id=result.template_id,
                        )
                    )

        duration_ms = int((perf_counter() - started) * 1000)
        success_count = sum(1 for item in results if item.success)
        failure_count = len(results) - success_count
        overall_status = (
            PLACEHOLDER_REPORT_STATUS
            if failure_count == 0 and success_count == len(results) and len(results) > 0
            else None
        )
        execution = ReportExecutionResult(
            plan_digest=plan.plan_digest,
            profile_name=plan.profile_name,
            results=tuple(results),
            duration_ms=duration_ms,
            template_count=len(results),
            success_count=success_count,
            failure_count=failure_count,
            overall_status=overall_status,
            warnings=tuple(warnings),
            errors=tuple(errors),
            metadata=MappingProxyType({"placeholder_pipeline": True}),
        )
        success = failure_count == 0 and not errors
        return ReportExecutionOutcome(
            success=success,
            message=(
                "Report pipeline executed successfully."
                if success
                else "Report pipeline execution failed."
            ),
            execution=execution,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def _build_report_context(
        self,
        context: RunContext,
        *,
        plan: ValidationPlan,
        certification_execution: CertificationExecutionResult,
        certification_result: CertificationResult,
    ) -> ReportContext:
        return ReportContext(
            run_id=context.run_id,
            profile_name=plan.profile_name,
            plan_digest=plan.plan_digest,
            protocol_major=context.protocol_major,
            protocol_minor=context.protocol_minor,
            execution_tier=context.execution_tier,
            certification_result=certification_result,
            certification_execution=certification_execution,
            configuration=MappingProxyType(dict(plan.configuration)),
            metadata=MappingProxyType({"run_metadata_keys": tuple(sorted(context.metadata))}),
        )
