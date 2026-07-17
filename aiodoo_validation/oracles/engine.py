"""Oracle engine — execute ValidationPlan oracle pipelines (Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import OracleErrorCode
from aiodoo_validation.domain.oracle import (
    OracleContext,
    OracleError,
    OracleExecutionOutcome,
    OracleExecutionResult,
    OracleResult,
)
from aiodoo_validation.oracles.registry import OracleRegistry
from aiodoo_validation.validation_plan.plan import ValidationPlan


@dataclass(frozen=True, slots=True)
class OracleEngine:
    """
    Execute registered oracles according to the attached ValidationPlan.

    The engine never decides which oracles belong to a profile — that is owned
    by the Coding Profile / ValidationPlan. This engine only resolves and runs
    enabled pipeline entries.
    """

    registry: OracleRegistry

    @classmethod
    def create_default(cls) -> OracleEngine:
        return cls(registry=OracleRegistry.create_default())

    def execute_oracles(self, context: RunContext) -> OracleExecutionOutcome:
        try:
            return self._execute_oracles(context)
        except OracleError as exc:
            return OracleExecutionOutcome(
                success=False,
                message="Oracle execution failed.",
                errors=(exc,),
            )
        except Exception as exc:  # noqa: BLE001 — oracle engine must never crash callers
            return OracleExecutionOutcome(
                success=False,
                message="Oracle execution failed.",
                errors=(
                    OracleError(
                        code=OracleErrorCode.EXECUTION_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _execute_oracles(self, context: RunContext) -> OracleExecutionOutcome:
        plan = context.validation_plan
        profile = context.validation_profile
        if plan is None:
            return OracleExecutionOutcome(
                success=False,
                message="Oracle execution failed.",
                errors=(
                    OracleError(
                        code=OracleErrorCode.MISSING_PLAN,
                        message="ValidationPlan is required before oracle execution.",
                        field="validation_plan",
                    ),
                ),
            )
        if profile is None:
            return OracleExecutionOutcome(
                success=False,
                message="Oracle execution failed.",
                errors=(
                    OracleError(
                        code=OracleErrorCode.MISSING_PROFILE,
                        message="Resolved profile is required before oracle execution.",
                        field="validation_profile",
                    ),
                ),
            )

        capability_error = self._validate_capabilities(plan)
        if capability_error is not None:
            return OracleExecutionOutcome(
                success=False,
                message="Oracle execution failed.",
                errors=(capability_error,),
            )

        started = perf_counter()
        results: list[OracleResult] = []
        errors: list[OracleError] = []
        warnings: list[str] = []

        oracle_context = self._build_oracle_context(context, plan)
        for stage in plan.oracle_pipeline:
            if not stage.enabled:
                continue
            try:
                oracle = self.registry.get(stage.stage_id)
            except OracleError as exc:
                errors.append(exc)
                results.append(
                    OracleResult(
                        oracle_id=stage.stage_id,
                        success=False,
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue

            profile_error = self._validate_oracle_profile(oracle.metadata.supported_profile, plan)
            if profile_error is not None:
                errors.append(profile_error)
                results.append(
                    OracleResult(
                        oracle_id=stage.stage_id,
                        success=False,
                        message=profile_error.message,
                        errors=(profile_error,),
                    )
                )
                continue

            try:
                result = oracle.execute(oracle_context)
            except OracleError as exc:
                errors.append(exc)
                results.append(
                    OracleResult(
                        oracle_id=stage.stage_id,
                        success=False,
                        message=exc.message,
                        errors=(exc,),
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 — isolate oracle failures
                wrapped = OracleError(
                    code=OracleErrorCode.EXECUTION_FAILURE,
                    message=f"Oracle {stage.stage_id!r} failed: {exc}",
                    oracle_id=stage.stage_id,
                )
                errors.append(wrapped)
                results.append(
                    OracleResult(
                        oracle_id=stage.stage_id,
                        success=False,
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
                        OracleError(
                            code=OracleErrorCode.EXECUTION_FAILURE,
                            message=result.message,
                            oracle_id=result.oracle_id,
                        )
                    )

        duration_ms = int((perf_counter() - started) * 1000)
        success_count = sum(1 for item in results if item.success)
        failure_count = len(results) - success_count
        execution = OracleExecutionResult(
            plan_digest=plan.plan_digest,
            profile_name=plan.profile_name,
            results=tuple(results),
            duration_ms=duration_ms,
            oracle_count=len(results),
            success_count=success_count,
            failure_count=failure_count,
            warnings=tuple(warnings),
            errors=tuple(errors),
            metadata=MappingProxyType({"placeholder_pipeline": True}),
        )
        success = failure_count == 0 and not errors
        return OracleExecutionOutcome(
            success=success,
            message=(
                "Oracle pipeline executed successfully."
                if success
                else "Oracle pipeline execution failed."
            ),
            execution=execution,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def _validate_capabilities(self, plan: ValidationPlan) -> OracleError | None:
        if not plan.capabilities.supports_oracles:
            return OracleError(
                code=OracleErrorCode.CAPABILITY_MISMATCH,
                message=(
                    f"ValidationPlan for profile {plan.profile_name!r} does not support oracles."
                ),
                field="capabilities.supports_oracles",
            )
        return None

    def _validate_oracle_profile(
        self,
        supported_profile: str,
        plan: ValidationPlan,
    ) -> OracleError | None:
        if supported_profile != plan.profile_name:
            return OracleError(
                code=OracleErrorCode.PROFILE_MISMATCH,
                message=(
                    f"Oracle supports profile {supported_profile!r} "
                    f"but plan is {plan.profile_name!r}."
                ),
                field="supported_profile",
            )
        return None

    def _build_oracle_context(
        self,
        context: RunContext,
        plan: ValidationPlan,
    ) -> OracleContext:
        return OracleContext(
            run_id=context.run_id,
            profile_name=plan.profile_name,
            plan_digest=plan.plan_digest,
            protocol_major=context.protocol_major,
            protocol_minor=context.protocol_minor,
            execution_tier=context.execution_tier,
            configuration=MappingProxyType(dict(plan.configuration)),
            artifact_bundle=context.artifact_bundle,
            inference_session=context.inference_session,
            metadata=MappingProxyType({"run_metadata_keys": tuple(sorted(context.metadata))}),
        )
