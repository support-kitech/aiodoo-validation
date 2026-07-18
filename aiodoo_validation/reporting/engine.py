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
                    message=(f"Report template {template.metadata.template_id!r} failed: {exc}"),
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
            metadata=MappingProxyType({"registry_pipeline": True}),
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
            run_summary=MappingProxyType(_build_run_summary(context)),
        )


def _build_run_summary(context: RunContext) -> dict[str, object]:
    """Machine-readable summary for richer production reports."""
    from aiodoo_validation.__version__ import __version__
    from aiodoo_validation.domain.enums import BehaviorStatus, ValidationKind
    from aiodoo_validation.domain.request import SUPPORTED_PROTOCOL_MAJOR
    from aiodoo_validation.execution import (
        certification_label,
        is_framework_only_tier,
        normalize_execution_tier,
    )

    oracle = context.oracle_execution
    scores = context.score_execution
    bench = context.benchmark_execution
    cert = context.certification_execution
    session = context.inference_session
    structural_ids: list[str] = []
    behavior_ids: list[str] = []
    if oracle is not None:
        for result in oracle.results:
            kind = str(result.metadata.get("validation_kind", "structural"))
            if kind == "behavioral":
                behavior_ids.append(result.oracle_id)
            else:
                structural_ids.append(result.oracle_id)

    if behavior_ids and oracle is not None:
        behavioral_results = [
            result
            for result in oracle.results
            if str(result.metadata.get("validation_kind", "structural")) == "behavioral"
        ]
        deferred_only = all(bool(result.metadata.get("deferred")) for result in behavioral_results)
        if deferred_only:
            behavior_status = BehaviorStatus.DEFERRED
            validation_kind = ValidationKind.STRUCTURAL.value
        else:
            behavior_status = BehaviorStatus.ACTIVE
            validation_kind = ValidationKind.BEHAVIORAL.value
    else:
        behavior_status = BehaviorStatus.DEFERRED
        validation_kind = ValidationKind.STRUCTURAL.value

    overall_certified = None if cert is None else cert.overall_certified
    certified_bool = bool(overall_certified) if overall_certified is not None else False
    label = certification_label(
        profile_name=context.request.profile_name,
        certified=certified_bool,
    )
    if overall_certified is True:
        overall_status = "certified"
    elif overall_certified is False:
        overall_status = "not_certified"
    else:
        overall_status = "unknown"

    tier = normalize_execution_tier(context.execution_tier)
    if is_framework_only_tier(tier):
        execution_mode = "framework"
    else:
        execution_mode = tier.value

    profile = context.validation_profile
    profile_version = "v1"
    if profile is not None:
        strategy = getattr(profile, "validation_strategy", None)
        if isinstance(strategy, str) and strategy.strip():
            profile_version = strategy

    return {
        # Convenience top-level fields for CLI / API / dashboard consumers
        "overall_status": overall_status,
        "overall_score": None if scores is None else scores.aggregate_score,
        "overall_certified": overall_certified,
        "validation_kind": validation_kind,
        "report_version": "1.1.0",
        "protocol_version": (f"{SUPPORTED_PROTOCOL_MAJOR}.{context.protocol_minor}"),
        "profile_version": profile_version,
        "execution_mode": execution_mode,
        "behavior_status": behavior_status.value,
        "certification_label": label,
        "repository_version": __version__,
        # Existing nested structures
        "execution_tier": context.execution_tier.value,
        "profile": context.request.profile_name,
        "warnings": tuple(context.warnings),
        "errors": tuple(context.errors),
        "timing_ms": {
            "oracle": None if oracle is None else oracle.duration_ms,
            "scoring": None if scores is None else scores.duration_ms,
            "benchmark": None if bench is None else bench.duration_ms,
            "certification": None if cert is None else cert.duration_ms,
        },
        "structural_validation": {
            "oracle_ids": tuple(structural_ids),
            "success_count": None if oracle is None else oracle.success_count,
            "failure_count": None if oracle is None else oracle.failure_count,
        },
        "behavior_validation": {
            "oracle_ids": tuple(behavior_ids),
            "enabled": bool(behavior_ids),
            "status": behavior_status.value,
        },
        "oracle_summary": None
        if oracle is None
        else {
            "oracle_count": oracle.oracle_count,
            "success_count": oracle.success_count,
            "failure_count": oracle.failure_count,
        },
        "score_summary": None
        if scores is None
        else {
            "policy_count": scores.policy_count,
            "aggregate_score": scores.aggregate_score,
            "success_count": scores.success_count,
        },
        "benchmark_summary": None
        if bench is None
        else {
            "policy_count": bench.policy_count,
            "aggregate_benchmark_score": bench.aggregate_benchmark_score,
            "success_count": bench.success_count,
        },
        "certification_decision": None
        if cert is None
        else {
            "overall_certified": cert.overall_certified,
            "certified_count": cert.certified_count,
            "aggregate_certification_score": cert.aggregate_certification_score,
        },
        "inference": None
        if session is None
        else {
            "runtime": session.runtime,
            "model_identifier": session.model_identifier,
            "adapter_type": session.adapter_type,
            "ready": session.ready,
        },
        "artifacts": {
            "base_model_ref": context.request.base_model_ref,
            "adapter_ref": context.request.adapter_ref,
            "merged_model_ref": context.request.merged_model_ref,
            "bundle_digest": None
            if context.artifact_bundle is None
            else context.artifact_bundle.bundle_digest,
        },
    }
