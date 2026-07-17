"""Scoring engine — consume OracleExecutionResult only (Phase 6)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ScoreErrorCode
from aiodoo_validation.domain.oracle import OracleExecutionResult, OracleResult
from aiodoo_validation.domain.scoring import (
    ScoreContext,
    ScoreError,
    ScoreExecutionOutcome,
    ScoreExecutionResult,
    ScoreResult,
)
from aiodoo_validation.scoring.registry import ScoringRegistry
from aiodoo_validation.validation_plan.plan import ValidationPlan


@dataclass(frozen=True, slots=True)
class ScoringEngine:
    """
    Execute registered scoring policies against OracleExecutionResult.

    Never inspects XML, Python, manifests, security files, or the filesystem.
    Never re-runs validation. Consumes oracle results only.
    """

    registry: ScoringRegistry

    @classmethod
    def create_default(cls) -> ScoringEngine:
        return cls(registry=ScoringRegistry.create_default())

    def score(self, context: RunContext) -> ScoreExecutionOutcome:
        try:
            return self._score(context)
        except ScoreError as exc:
            return ScoreExecutionOutcome(
                success=False,
                message="Scoring failed.",
                errors=(exc,),
            )
        except Exception as exc:  # noqa: BLE001 — scoring engine must never crash callers
            return ScoreExecutionOutcome(
                success=False,
                message="Scoring failed.",
                errors=(
                    ScoreError(
                        code=ScoreErrorCode.EXECUTION_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _score(self, context: RunContext) -> ScoreExecutionOutcome:
        plan = context.validation_plan
        profile = context.validation_profile
        oracle_execution = context.oracle_execution

        if plan is None:
            return ScoreExecutionOutcome(
                success=False,
                message="Scoring failed.",
                errors=(
                    ScoreError(
                        code=ScoreErrorCode.MISSING_PLAN,
                        message="ValidationPlan is required before scoring.",
                        field="validation_plan",
                    ),
                ),
            )
        if profile is None:
            return ScoreExecutionOutcome(
                success=False,
                message="Scoring failed.",
                errors=(
                    ScoreError(
                        code=ScoreErrorCode.MISSING_PROFILE,
                        message="Resolved profile is required before scoring.",
                        field="validation_profile",
                    ),
                ),
            )
        if oracle_execution is None:
            return ScoreExecutionOutcome(
                success=False,
                message="Scoring failed.",
                errors=(
                    ScoreError(
                        code=ScoreErrorCode.MISSING_ORACLE_RESULTS,
                        message="OracleExecutionResult is required before scoring.",
                        field="oracle_execution",
                    ),
                ),
            )

        if not plan.capabilities.supports_scoring:
            return ScoreExecutionOutcome(
                success=False,
                message="Scoring failed.",
                errors=(
                    ScoreError(
                        code=ScoreErrorCode.CAPABILITY_MISMATCH,
                        message=(
                            f"ValidationPlan for profile {plan.profile_name!r} "
                            "does not support scoring."
                        ),
                        field="capabilities.supports_scoring",
                    ),
                ),
            )

        oracle_by_id = {result.oracle_id: result for result in oracle_execution.results}
        started = perf_counter()
        results: list[ScoreResult] = []
        errors: list[ScoreError] = []
        warnings: list[str] = []

        for stage in plan.scoring_pipeline:
            if not stage.enabled:
                continue
            try:
                policy = self.registry.get(stage.stage_id)
            except ScoreError as exc:
                errors.append(exc)
                results.append(
                    ScoreResult(
                        policy_id=stage.stage_id,
                        source_oracle_id="",
                        success=False,
                        score=0.0,
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue

            if policy.metadata.supported_profile != plan.profile_name:
                mismatch = ScoreError(
                    code=ScoreErrorCode.PROFILE_MISMATCH,
                    message=(
                        f"Score policy supports profile "
                        f"{policy.metadata.supported_profile!r} "
                        f"but plan is {plan.profile_name!r}."
                    ),
                    field="supported_profile",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(mismatch)
                results.append(
                    ScoreResult(
                        policy_id=policy.metadata.policy_id,
                        source_oracle_id=policy.metadata.source_oracle_id,
                        success=False,
                        score=0.0,
                        message=mismatch.message,
                        errors=(mismatch,),
                    )
                )
                continue

            oracle_result = oracle_by_id.get(policy.metadata.source_oracle_id)
            if oracle_result is None:
                missing = ScoreError(
                    code=ScoreErrorCode.ORACLE_RESULT_MISSING,
                    message=(
                        f"No OracleResult for source oracle "
                        f"{policy.metadata.source_oracle_id!r}."
                    ),
                    field="source_oracle_id",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(missing)
                results.append(
                    ScoreResult(
                        policy_id=policy.metadata.policy_id,
                        source_oracle_id=policy.metadata.source_oracle_id,
                        success=False,
                        score=0.0,
                        message=missing.message,
                        errors=(missing,),
                    )
                )
                continue

            score_context = self._build_score_context(
                context,
                plan=plan,
                oracle_execution=oracle_execution,
                oracle_result=oracle_result,
            )
            try:
                result = policy.score(score_context)
            except ScoreError as exc:
                errors.append(exc)
                results.append(
                    ScoreResult(
                        policy_id=policy.metadata.policy_id,
                        source_oracle_id=policy.metadata.source_oracle_id,
                        success=False,
                        score=0.0,
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 — isolate policy failures
                wrapped = ScoreError(
                    code=ScoreErrorCode.EXECUTION_FAILURE,
                    message=f"Score policy {policy.metadata.policy_id!r} failed: {exc}",
                    policy_id=policy.metadata.policy_id,
                )
                errors.append(wrapped)
                results.append(
                    ScoreResult(
                        policy_id=policy.metadata.policy_id,
                        source_oracle_id=policy.metadata.source_oracle_id,
                        success=False,
                        score=0.0,
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
                        ScoreError(
                            code=ScoreErrorCode.EXECUTION_FAILURE,
                            message=result.message,
                            policy_id=result.policy_id,
                        )
                    )

        duration_ms = int((perf_counter() - started) * 1000)
        success_count = sum(1 for item in results if item.success)
        failure_count = len(results) - success_count
        successful_scores = tuple(item.score for item in results if item.success)
        aggregate = (
            sum(successful_scores) / len(successful_scores) if successful_scores else None
        )
        execution = ScoreExecutionResult(
            plan_digest=plan.plan_digest,
            profile_name=plan.profile_name,
            results=tuple(results),
            duration_ms=duration_ms,
            policy_count=len(results),
            success_count=success_count,
            failure_count=failure_count,
            aggregate_score=aggregate,
            warnings=tuple(warnings),
            errors=tuple(errors),
            metadata=MappingProxyType({"placeholder_pipeline": True}),
        )
        success = failure_count == 0 and not errors
        return ScoreExecutionOutcome(
            success=success,
            message=(
                "Scoring pipeline executed successfully."
                if success
                else "Scoring pipeline execution failed."
            ),
            execution=execution,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def _build_score_context(
        self,
        context: RunContext,
        *,
        plan: ValidationPlan,
        oracle_execution: OracleExecutionResult,
        oracle_result: OracleResult,
    ) -> ScoreContext:
        return ScoreContext(
            run_id=context.run_id,
            profile_name=plan.profile_name,
            plan_digest=plan.plan_digest,
            protocol_major=context.protocol_major,
            protocol_minor=context.protocol_minor,
            execution_tier=context.execution_tier,
            oracle_result=oracle_result,
            oracle_execution=oracle_execution,
            configuration=MappingProxyType(dict(plan.configuration)),
            metadata=MappingProxyType({"run_metadata_keys": tuple(sorted(context.metadata))}),
        )
