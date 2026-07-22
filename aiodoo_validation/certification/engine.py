"""Certification engine — consume BenchmarkExecutionResult only (Phase 8)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.certification.registry import CertificationRegistry
from aiodoo_validation.contract.version_check import (
    VALIDATION_CONTRACT_VERSION,
    ContractVersionError,
    ensure_contract_compatible,
)
from aiodoo_validation.domain.benchmark import BenchmarkExecutionResult, BenchmarkResult
from aiodoo_validation.domain.certification import (
    CertificationContext,
    CertificationError,
    CertificationExecutionOutcome,
    CertificationExecutionResult,
    CertificationResult,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import CertificationErrorCode
from aiodoo_validation.validation_plan.plan import ValidationPlan


@dataclass(frozen=True, slots=True)
class CertificationEngine:
    """
    Execute registered certification policies against BenchmarkExecutionResult.

    Never inspects XML, Python, manifests, security files, or the filesystem.
    Never re-runs validation, scoring, or benchmarking. Consumes benchmark
    results only.
    """

    registry: CertificationRegistry

    @classmethod
    def create_default(cls) -> CertificationEngine:
        return cls(registry=CertificationRegistry.create_default())

    def certify(self, context: RunContext) -> CertificationExecutionOutcome:
        try:
            return self._certify(context)
        except CertificationError as exc:
            return CertificationExecutionOutcome(
                success=False,
                message="Certification failed.",
                errors=(exc,),
            )
        except Exception as exc:  # noqa: BLE001 — certification engine must never crash callers
            return CertificationExecutionOutcome(
                success=False,
                message="Certification failed.",
                errors=(
                    CertificationError(
                        code=CertificationErrorCode.EXECUTION_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _certify(self, context: RunContext) -> CertificationExecutionOutcome:
        try:
            ensure_contract_compatible()
        except ContractVersionError as exc:
            return CertificationExecutionOutcome(
                success=False,
                message="Certification failed.",
                errors=(
                    CertificationError(
                        code=CertificationErrorCode.CONTRACT_VERSION_INCOMPATIBLE,
                        message=str(exc),
                        field="contract_version",
                    ),
                ),
            )

        plan = context.validation_plan
        profile = context.validation_profile
        benchmark_execution = context.benchmark_execution

        if plan is None:
            return CertificationExecutionOutcome(
                success=False,
                message="Certification failed.",
                errors=(
                    CertificationError(
                        code=CertificationErrorCode.MISSING_PLAN,
                        message="ValidationPlan is required before certification.",
                        field="validation_plan",
                    ),
                ),
            )
        if profile is None:
            return CertificationExecutionOutcome(
                success=False,
                message="Certification failed.",
                errors=(
                    CertificationError(
                        code=CertificationErrorCode.MISSING_PROFILE,
                        message="Resolved profile is required before certification.",
                        field="validation_profile",
                    ),
                ),
            )
        if benchmark_execution is None:
            return CertificationExecutionOutcome(
                success=False,
                message="Certification failed.",
                errors=(
                    CertificationError(
                        code=CertificationErrorCode.MISSING_BENCHMARK_RESULTS,
                        message="BenchmarkExecutionResult is required before certification.",
                        field="benchmark_execution",
                    ),
                ),
            )

        if not plan.capabilities.supports_certification:
            return CertificationExecutionOutcome(
                success=False,
                message="Certification failed.",
                errors=(
                    CertificationError(
                        code=CertificationErrorCode.CAPABILITY_MISMATCH,
                        message=(
                            f"ValidationPlan for profile {plan.profile_name!r} "
                            "does not support certification."
                        ),
                        field="capabilities.supports_certification",
                    ),
                ),
            )

        benchmark_by_id = {result.policy_id: result for result in benchmark_execution.results}
        started = perf_counter()
        results: list[CertificationResult] = []
        errors: list[CertificationError] = []
        warnings: list[str] = []

        for stage in plan.certification_pipeline:
            if not stage.enabled:
                continue
            try:
                policy = self.registry.get(stage.stage_id)
            except CertificationError as exc:
                errors.append(exc)
                results.append(
                    CertificationResult(
                        policy_id=stage.stage_id,
                        source_benchmark_policy_id="",
                        success=False,
                        certified=False,
                        certification_score=0.0,
                        certification_level="FAIL",
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue

            if policy.metadata.supported_profile != plan.profile_name:
                mismatch = CertificationError(
                    code=CertificationErrorCode.PROFILE_MISMATCH,
                    message=(
                        f"Certification policy supports profile "
                        f"{policy.metadata.supported_profile!r} "
                        f"but plan is {plan.profile_name!r}."
                    ),
                    field="supported_profile",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(mismatch)
                results.append(
                    CertificationResult(
                        policy_id=policy.metadata.policy_id,
                        source_benchmark_policy_id=policy.metadata.source_benchmark_policy_id,
                        success=False,
                        certified=False,
                        certification_score=0.0,
                        certification_level="FAIL",
                        message=mismatch.message,
                        errors=(mismatch,),
                    )
                )
                continue

            benchmark_result = benchmark_by_id.get(policy.metadata.source_benchmark_policy_id)
            if benchmark_result is None:
                missing = CertificationError(
                    code=CertificationErrorCode.BENCHMARK_RESULT_MISSING,
                    message=(
                        f"No BenchmarkResult for source benchmark policy "
                        f"{policy.metadata.source_benchmark_policy_id!r}."
                    ),
                    field="source_benchmark_policy_id",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(missing)
                results.append(
                    CertificationResult(
                        policy_id=policy.metadata.policy_id,
                        source_benchmark_policy_id=policy.metadata.source_benchmark_policy_id,
                        success=False,
                        certified=False,
                        certification_score=0.0,
                        certification_level="FAIL",
                        message=missing.message,
                        errors=(missing,),
                    )
                )
                continue

            certification_context = self._build_certification_context(
                context,
                plan=plan,
                benchmark_execution=benchmark_execution,
                benchmark_result=benchmark_result,
            )
            try:
                result = policy.certify(certification_context)
            except CertificationError as exc:
                errors.append(exc)
                results.append(
                    CertificationResult(
                        policy_id=policy.metadata.policy_id,
                        source_benchmark_policy_id=policy.metadata.source_benchmark_policy_id,
                        success=False,
                        certified=False,
                        certification_score=0.0,
                        certification_level="FAIL",
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 — isolate policy failures
                wrapped = CertificationError(
                    code=CertificationErrorCode.EXECUTION_FAILURE,
                    message=(f"Certification policy {policy.metadata.policy_id!r} failed: {exc}"),
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(wrapped)
                results.append(
                    CertificationResult(
                        policy_id=policy.metadata.policy_id,
                        source_benchmark_policy_id=policy.metadata.source_benchmark_policy_id,
                        success=False,
                        certified=False,
                        certification_score=0.0,
                        certification_level="FAIL",
                        message=wrapped.message,
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
                        CertificationError(
                            code=CertificationErrorCode.EXECUTION_FAILURE,
                            message=result.message,
                            policy_id=result.policy_id,
                        )
                    )

        duration_ms = int((perf_counter() - started) * 1000)
        success_count = sum(1 for item in results if item.success)
        failure_count = len(results) - success_count
        certified_count = sum(1 for item in results if item.success and item.certified)
        successful_scores = tuple(item.certification_score for item in results if item.success)
        aggregate = sum(successful_scores) / len(successful_scores) if successful_scores else None
        overall_certified = (
            failure_count == 0 and certified_count == len(results) and len(results) > 0
        )
        execution = CertificationExecutionResult(
            plan_digest=plan.plan_digest,
            profile_name=plan.profile_name,
            results=tuple(results),
            duration_ms=duration_ms,
            policy_count=len(results),
            success_count=success_count,
            failure_count=failure_count,
            certified_count=certified_count,
            overall_certified=overall_certified if results else None,
            aggregate_certification_score=aggregate,
            warnings=tuple(warnings),
            errors=tuple(errors),
            metadata=MappingProxyType(
                {
                    "registry_pipeline": True,
                    "contract_version": VALIDATION_CONTRACT_VERSION,
                    "capability": plan.profile_name,
                }
            ),
        )
        success = failure_count == 0 and not errors
        return CertificationExecutionOutcome(
            success=success,
            message=(
                "Certification pipeline executed successfully."
                if success
                else "Certification pipeline execution failed."
            ),
            execution=execution,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def _build_certification_context(
        self,
        context: RunContext,
        *,
        plan: ValidationPlan,
        benchmark_execution: BenchmarkExecutionResult,
        benchmark_result: BenchmarkResult,
    ) -> CertificationContext:
        return CertificationContext(
            run_id=context.run_id,
            profile_name=plan.profile_name,
            plan_digest=plan.plan_digest,
            protocol_major=context.protocol_major,
            protocol_minor=context.protocol_minor,
            execution_tier=context.execution_tier,
            benchmark_result=benchmark_result,
            benchmark_execution=benchmark_execution,
            score_execution=context.score_execution,
            configuration=MappingProxyType(dict(plan.configuration)),
            metadata=MappingProxyType({"run_metadata_keys": tuple(sorted(context.metadata))}),
        )
