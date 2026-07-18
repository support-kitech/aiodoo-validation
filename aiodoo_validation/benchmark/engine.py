"""Benchmark engine — consume ScoreExecutionResult only (Phase 7)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.benchmark.registry import BenchmarkRegistry
from aiodoo_validation.domain.benchmark import (
    BenchmarkContext,
    BenchmarkError,
    BenchmarkExecutionOutcome,
    BenchmarkExecutionResult,
    BenchmarkResult,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import BenchmarkErrorCode
from aiodoo_validation.domain.scoring import ScoreExecutionResult, ScoreResult
from aiodoo_validation.validation_plan.plan import ValidationPlan


@dataclass(frozen=True, slots=True)
class BenchmarkEngine:
    """
    Execute registered benchmark policies against ScoreExecutionResult.

    Never inspects XML, Python, manifests, security files, or the filesystem.
    Never re-runs validation or scoring. Consumes score results only.
    """

    registry: BenchmarkRegistry

    @classmethod
    def create_default(cls) -> BenchmarkEngine:
        return cls(registry=BenchmarkRegistry.create_default())

    def benchmark(self, context: RunContext) -> BenchmarkExecutionOutcome:
        try:
            return self._benchmark(context)
        except BenchmarkError as exc:
            return BenchmarkExecutionOutcome(
                success=False,
                message="Benchmarking failed.",
                errors=(exc,),
            )
        except Exception as exc:  # noqa: BLE001 — benchmark engine must never crash callers
            return BenchmarkExecutionOutcome(
                success=False,
                message="Benchmarking failed.",
                errors=(
                    BenchmarkError(
                        code=BenchmarkErrorCode.EXECUTION_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _benchmark(self, context: RunContext) -> BenchmarkExecutionOutcome:
        plan = context.validation_plan
        profile = context.validation_profile
        score_execution = context.score_execution

        if plan is None:
            return BenchmarkExecutionOutcome(
                success=False,
                message="Benchmarking failed.",
                errors=(
                    BenchmarkError(
                        code=BenchmarkErrorCode.MISSING_PLAN,
                        message="ValidationPlan is required before benchmarking.",
                        field="validation_plan",
                    ),
                ),
            )
        if profile is None:
            return BenchmarkExecutionOutcome(
                success=False,
                message="Benchmarking failed.",
                errors=(
                    BenchmarkError(
                        code=BenchmarkErrorCode.MISSING_PROFILE,
                        message="Resolved profile is required before benchmarking.",
                        field="validation_profile",
                    ),
                ),
            )
        if score_execution is None:
            return BenchmarkExecutionOutcome(
                success=False,
                message="Benchmarking failed.",
                errors=(
                    BenchmarkError(
                        code=BenchmarkErrorCode.MISSING_SCORE_RESULTS,
                        message="ScoreExecutionResult is required before benchmarking.",
                        field="score_execution",
                    ),
                ),
            )

        if not plan.capabilities.supports_benchmark:
            return BenchmarkExecutionOutcome(
                success=False,
                message="Benchmarking failed.",
                errors=(
                    BenchmarkError(
                        code=BenchmarkErrorCode.CAPABILITY_MISMATCH,
                        message=(
                            f"ValidationPlan for profile {plan.profile_name!r} "
                            "does not support benchmarking."
                        ),
                        field="capabilities.supports_benchmark",
                    ),
                ),
            )

        score_by_id = {result.policy_id: result for result in score_execution.results}
        started = perf_counter()
        results: list[BenchmarkResult] = []
        errors: list[BenchmarkError] = []
        warnings: list[str] = []

        for stage in plan.benchmark_pipeline:
            if not stage.enabled:
                continue
            try:
                policy = self.registry.get(stage.stage_id)
            except BenchmarkError as exc:
                errors.append(exc)
                results.append(
                    BenchmarkResult(
                        policy_id=stage.stage_id,
                        source_score_policy_id="",
                        success=False,
                        benchmark_score=0.0,
                        benchmark_pass=False,
                        benchmark_rank=0,
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue

            if policy.metadata.supported_profile != plan.profile_name:
                mismatch = BenchmarkError(
                    code=BenchmarkErrorCode.PROFILE_MISMATCH,
                    message=(
                        f"Benchmark policy supports profile "
                        f"{policy.metadata.supported_profile!r} "
                        f"but plan is {plan.profile_name!r}."
                    ),
                    field="supported_profile",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(mismatch)
                results.append(
                    BenchmarkResult(
                        policy_id=policy.metadata.policy_id,
                        source_score_policy_id=policy.metadata.source_score_policy_id,
                        success=False,
                        benchmark_score=0.0,
                        benchmark_pass=False,
                        benchmark_rank=0,
                        message=mismatch.message,
                        errors=(mismatch,),
                    )
                )
                continue

            score_result = score_by_id.get(policy.metadata.source_score_policy_id)
            if score_result is None:
                missing = BenchmarkError(
                    code=BenchmarkErrorCode.SCORE_RESULT_MISSING,
                    message=(
                        f"No ScoreResult for source score policy "
                        f"{policy.metadata.source_score_policy_id!r}."
                    ),
                    field="source_score_policy_id",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(missing)
                results.append(
                    BenchmarkResult(
                        policy_id=policy.metadata.policy_id,
                        source_score_policy_id=policy.metadata.source_score_policy_id,
                        success=False,
                        benchmark_score=0.0,
                        benchmark_pass=False,
                        benchmark_rank=0,
                        message=missing.message,
                        errors=(missing,),
                    )
                )
                continue

            benchmark_context = self._build_benchmark_context(
                context,
                plan=plan,
                score_execution=score_execution,
                score_result=score_result,
            )
            try:
                result = policy.benchmark(benchmark_context)
            except BenchmarkError as exc:
                errors.append(exc)
                results.append(
                    BenchmarkResult(
                        policy_id=policy.metadata.policy_id,
                        source_score_policy_id=policy.metadata.source_score_policy_id,
                        success=False,
                        benchmark_score=0.0,
                        benchmark_pass=False,
                        benchmark_rank=0,
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 — isolate policy failures
                wrapped = BenchmarkError(
                    code=BenchmarkErrorCode.EXECUTION_FAILURE,
                    message=f"Benchmark policy {policy.metadata.policy_id!r} failed: {exc}",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(wrapped)
                results.append(
                    BenchmarkResult(
                        policy_id=policy.metadata.policy_id,
                        source_score_policy_id=policy.metadata.source_score_policy_id,
                        success=False,
                        benchmark_score=0.0,
                        benchmark_pass=False,
                        benchmark_rank=0,
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
                        BenchmarkError(
                            code=BenchmarkErrorCode.EXECUTION_FAILURE,
                            message=result.message,
                            policy_id=result.policy_id,
                        )
                    )

        duration_ms = int((perf_counter() - started) * 1000)
        success_count = sum(1 for item in results if item.success)
        failure_count = len(results) - success_count
        successful_scores = tuple(item.benchmark_score for item in results if item.success)
        aggregate = sum(successful_scores) / len(successful_scores) if successful_scores else None
        execution = BenchmarkExecutionResult(
            plan_digest=plan.plan_digest,
            profile_name=plan.profile_name,
            results=tuple(results),
            duration_ms=duration_ms,
            policy_count=len(results),
            success_count=success_count,
            failure_count=failure_count,
            aggregate_benchmark_score=aggregate,
            warnings=tuple(warnings),
            errors=tuple(errors),
            metadata=MappingProxyType({"registry_pipeline": True}),
        )
        success = failure_count == 0 and not errors
        return BenchmarkExecutionOutcome(
            success=success,
            message=(
                "Benchmark pipeline executed successfully."
                if success
                else "Benchmark pipeline execution failed."
            ),
            execution=execution,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def _build_benchmark_context(
        self,
        context: RunContext,
        *,
        plan: ValidationPlan,
        score_execution: ScoreExecutionResult,
        score_result: ScoreResult,
    ) -> BenchmarkContext:
        return BenchmarkContext(
            run_id=context.run_id,
            profile_name=plan.profile_name,
            plan_digest=plan.plan_digest,
            protocol_major=context.protocol_major,
            protocol_minor=context.protocol_minor,
            execution_tier=context.execution_tier,
            score_result=score_result,
            score_execution=score_execution,
            configuration=MappingProxyType(dict(plan.configuration)),
            metadata=MappingProxyType({"run_metadata_keys": tuple(sorted(context.metadata))}),
        )
