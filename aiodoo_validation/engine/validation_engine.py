"""Validation Engine — orchestrates the frozen TDD lifecycle."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from aiodoo_validation.domain.benchmark import BenchmarkExecutionOutcome
from aiodoo_validation.domain.certification import CertificationExecutionOutcome
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ExitStatus, StageStatus, ValidationStage
from aiodoo_validation.domain.inference import InferenceInitializationOutcome
from aiodoo_validation.domain.oracle import OracleExecutionOutcome
from aiodoo_validation.domain.profile import ProfileResolutionOutcome
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.resolution import ArtifactResolutionOutcome
from aiodoo_validation.domain.result import ValidationRunResult
from aiodoo_validation.domain.scoring import ScoreExecutionOutcome
from aiodoo_validation.domain.stage import PlaceholderStageResult, StageRecord
from aiodoo_validation.engine.protocol import negotiate_protocol
from aiodoo_validation.exceptions import (
    AiodooValidationError,
    InvalidRequestError,
    PipelineError,
    ProtocolError,
)
from aiodoo_validation.inference import MockModelRuntime, RealInferenceRunner
from aiodoo_validation.ports import (
    ArtifactResolverPort,
    BenchmarkEnginePort,
    CertificationEnginePort,
    InferenceRunnerPort,
    OracleRunnerPort,
    ProfileEnginePort,
    ReportGeneratorPort,
    ScoringEnginePort,
)
from aiodoo_validation.resolution.filesystem import FilesystemArtifactResolver
from aiodoo_validation.stubs import StubPipelineComponents

_PortReturn = TypeVar("_PortReturn", bound=PlaceholderStageResult)
_StageExecutor = Callable[[RunContext], PlaceholderStageResult]

PIPELINE_STAGE_ORDER: tuple[ValidationStage, ...] = (
    ValidationStage.LOAD_REQUEST,
    ValidationStage.VALIDATE_REQUEST,
    ValidationStage.RESOLVE_ARTIFACTS,
    ValidationStage.RESOLVE_PROFILE,
    ValidationStage.INITIALIZE_INFERENCE,
    ValidationStage.RUN_VALIDATION,
    ValidationStage.SCORING,
    ValidationStage.BENCHMARK,
    ValidationStage.CERTIFICATION,
    ValidationStage.REPORT,
    ValidationStage.EXIT,
)


class ValidationEngine:
    """
    Production validation orchestrator skeleton.

    Executes the complete lifecycle using injected ports. Phase 8 wires the
    Certification Engine through ``CertificationEnginePort`` while report
    generation remains stubbed.
    """

    def __init__(
        self,
        *,
        artifact_resolver: ArtifactResolverPort,
        profile_engine: ProfileEnginePort,
        inference_runner: InferenceRunnerPort,
        oracle_runner: OracleRunnerPort,
        scoring_engine: ScoringEnginePort,
        benchmark_engine: BenchmarkEnginePort,
        certification_engine: CertificationEnginePort,
        report_generator: ReportGeneratorPort,
    ) -> None:
        self._artifact_resolver = artifact_resolver
        self._profile_engine = profile_engine
        self._inference_runner = inference_runner
        self._oracle_runner = oracle_runner
        self._scoring_engine = scoring_engine
        self._benchmark_engine = benchmark_engine
        self._certification_engine = certification_engine
        self._report_generator = report_generator

    @classmethod
    def with_stubs(cls) -> ValidationEngine:
        """Construct an engine wired with stub downstream ports."""
        stubs = StubPipelineComponents.create()
        return cls(
            artifact_resolver=stubs.artifact_resolver,
            profile_engine=stubs.profile_engine,
            inference_runner=stubs.inference_runner,
            oracle_runner=stubs.oracle_runner,
            scoring_engine=stubs.scoring_engine,
            benchmark_engine=stubs.benchmark_engine,
            certification_engine=stubs.certification_engine,
            report_generator=stubs.report_generator,
        )

    @classmethod
    def with_filesystem(cls) -> ValidationEngine:
        """Construct an engine with a real filesystem artifact resolver."""
        stubs = StubPipelineComponents.create()
        return cls(
            artifact_resolver=FilesystemArtifactResolver.create_default(),
            profile_engine=stubs.profile_engine,
            inference_runner=stubs.inference_runner,
            oracle_runner=stubs.oracle_runner,
            scoring_engine=stubs.scoring_engine,
            benchmark_engine=stubs.benchmark_engine,
            certification_engine=stubs.certification_engine,
            report_generator=stubs.report_generator,
        )

    @classmethod
    def with_mock_inference(cls) -> ValidationEngine:
        """Construct an engine with filesystem artifacts and mock inference."""
        stubs = StubPipelineComponents.create()
        return cls(
            artifact_resolver=FilesystemArtifactResolver.create_default(),
            profile_engine=stubs.profile_engine,
            inference_runner=RealInferenceRunner(runtime=MockModelRuntime()),
            oracle_runner=stubs.oracle_runner,
            scoring_engine=stubs.scoring_engine,
            benchmark_engine=stubs.benchmark_engine,
            certification_engine=stubs.certification_engine,
            report_generator=stubs.report_generator,
        )

    def run(self, request: ValidationRequest) -> ValidationRunResult:
        """Execute the full validation lifecycle for the given request."""
        context = RunContext.begin(request)
        try:
            context = self._execute_lifecycle(context)
            exit_status = context.exit_status or ExitStatus.NOT_CERTIFIED
            message = (
                "Validation lifecycle completed."
                if exit_status is not ExitStatus.FAILED
                else "Validation lifecycle failed."
            )
            return ValidationRunResult(
                exit_status=exit_status,
                run_context=context,
                message=message,
                completed_at=datetime.now(UTC),
            )
        except InvalidRequestError as exc:
            return self._error_result(context, ExitStatus.INVALID_REQUEST, str(exc))
        except ProtocolError as exc:
            return self._error_result(context, ExitStatus.INVALID_REQUEST, str(exc))
        except PipelineError as exc:
            return self._error_result(context, ExitStatus.FAILED, str(exc))
        except AiodooValidationError as exc:
            return self._error_result(context, ExitStatus.INTERNAL_ERROR, str(exc))

    def _execute_lifecycle(self, context: RunContext) -> RunContext:
        for stage in PIPELINE_STAGE_ORDER:
            context = context.with_stage(stage)
            if stage == ValidationStage.LOAD_REQUEST:
                context = self._run_internal_stage(
                    context,
                    stage,
                    lambda ctx: self._load_request(ctx),
                )
            elif stage == ValidationStage.VALIDATE_REQUEST:
                context = self._run_internal_stage(
                    context,
                    stage,
                    lambda ctx: self._validate_request(ctx),
                )
            elif stage == ValidationStage.RESOLVE_ARTIFACTS:
                context = self._run_artifact_stage(context)
                if context.exit_status is ExitStatus.FAILED:
                    return self._run_failed_exit(context)
            elif stage == ValidationStage.RESOLVE_PROFILE:
                context = self._run_profile_stage(context)
                if context.exit_status is ExitStatus.FAILED:
                    return self._run_failed_exit(context)
            elif stage == ValidationStage.INITIALIZE_INFERENCE:
                context = self._run_inference_stage(context)
                if context.exit_status is ExitStatus.FAILED:
                    return self._run_failed_exit(context)
            elif stage == ValidationStage.RUN_VALIDATION:
                context = self._run_oracle_stage(context)
                if context.exit_status is ExitStatus.FAILED:
                    return self._run_failed_exit(context)
            elif stage == ValidationStage.SCORING:
                context = self._run_scoring_stage(context)
                if context.exit_status is ExitStatus.FAILED:
                    return self._run_failed_exit(context)
            elif stage == ValidationStage.BENCHMARK:
                context = self._run_benchmark_stage(context)
                if context.exit_status is ExitStatus.FAILED:
                    return self._run_failed_exit(context)
            elif stage == ValidationStage.CERTIFICATION:
                context = self._run_certification_stage(context)
                if context.exit_status is ExitStatus.FAILED:
                    return self._run_failed_exit(context)
            elif stage == ValidationStage.EXIT:
                context = self._run_exit(context)
            else:
                if context.exit_status is ExitStatus.FAILED:
                    continue
                context = self._run_port_stage(context, stage, self._executor_for(stage))
        return context

    def _executor_for(self, stage: ValidationStage) -> _StageExecutor:
        executors: dict[ValidationStage, _StageExecutor] = {
            ValidationStage.REPORT: self._report_generator.generate_report,
        }
        return executors[stage]

    def _load_request(self, context: RunContext) -> PlaceholderStageResult:
        return PlaceholderStageResult(
            stage=ValidationStage.LOAD_REQUEST,
            status=StageStatus.SUCCEEDED,
            message="validation request loaded",
            data=context.request.metadata,
        )

    def _validate_request(self, context: RunContext) -> PlaceholderStageResult:
        major, minor = negotiate_protocol(context.request)
        return PlaceholderStageResult(
            stage=ValidationStage.VALIDATE_REQUEST,
            status=StageStatus.SUCCEEDED,
            message="validation request accepted",
            data={"protocol_major": major, "protocol_minor": minor},
        )

    def _run_artifact_stage(self, context: RunContext) -> RunContext:
        outcome = self._artifact_resolver.resolve(context)
        return self._apply_artifact_outcome(context, outcome)

    def _apply_artifact_outcome(
        self,
        context: RunContext,
        outcome: ArtifactResolutionOutcome,
    ) -> RunContext:
        result = outcome.to_stage_result()
        updated = self._record_stage(context, ValidationStage.RESOLVE_ARTIFACTS, result)
        for warning in outcome.warnings:
            updated = updated.with_warning(warning)
        if outcome.success and outcome.bundle is not None:
            return updated.with_artifact_bundle(outcome.bundle)
        for error in outcome.errors:
            updated = updated.with_error(f"{error.code.value}: {error.message}")
        return updated.with_exit_status(ExitStatus.FAILED)

    def _run_profile_stage(self, context: RunContext) -> RunContext:
        outcome = self._profile_engine.resolve_profile(context)
        return self._apply_profile_outcome(context, outcome)

    def _apply_profile_outcome(
        self,
        context: RunContext,
        outcome: ProfileResolutionOutcome,
    ) -> RunContext:
        result = outcome.to_stage_result()
        updated = self._record_stage(context, ValidationStage.RESOLVE_PROFILE, result)
        for warning in outcome.warnings:
            updated = updated.with_warning(warning)
        if (
            outcome.success
            and outcome.profile is not None
            and outcome.plan is not None
        ):
            return (
                updated.with_validation_profile(outcome.profile)
                .with_validation_plan(outcome.plan)
            )
        for error in outcome.errors:
            updated = updated.with_error(f"{error.code.value}: {error.message}")
        return updated.with_exit_status(ExitStatus.FAILED)

    def _run_inference_stage(self, context: RunContext) -> RunContext:
        outcome = self._inference_runner.initialize(context)
        return self._apply_inference_outcome(context, outcome)

    def _apply_inference_outcome(
        self,
        context: RunContext,
        outcome: InferenceInitializationOutcome,
    ) -> RunContext:
        result = outcome.to_stage_result()
        updated = self._record_stage(context, ValidationStage.INITIALIZE_INFERENCE, result)
        for warning in outcome.warnings:
            updated = updated.with_warning(warning)
        if outcome.success and outcome.session is not None:
            return updated.with_inference_session(outcome.session)
        for error in outcome.errors:
            updated = updated.with_error(f"{error.code.value}: {error.message}")
        return updated.with_exit_status(ExitStatus.FAILED)

    def _run_oracle_stage(self, context: RunContext) -> RunContext:
        outcome = self._oracle_runner.execute_oracles(context)
        return self._apply_oracle_outcome(context, outcome)

    def _apply_oracle_outcome(
        self,
        context: RunContext,
        outcome: OracleExecutionOutcome,
    ) -> RunContext:
        result = outcome.to_stage_result()
        updated = self._record_stage(context, ValidationStage.RUN_VALIDATION, result)
        for warning in outcome.warnings:
            updated = updated.with_warning(warning)
        if outcome.success and outcome.execution is not None:
            return updated.with_oracle_execution(outcome.execution)
        for error in outcome.errors:
            detail = f"{error.code.value}: {error.message}"
            updated = updated.with_error(detail)
        return updated.with_exit_status(ExitStatus.FAILED)

    def _run_scoring_stage(self, context: RunContext) -> RunContext:
        outcome = self._scoring_engine.score(context)
        return self._apply_scoring_outcome(context, outcome)

    def _apply_scoring_outcome(
        self,
        context: RunContext,
        outcome: ScoreExecutionOutcome,
    ) -> RunContext:
        result = outcome.to_stage_result()
        updated = self._record_stage(context, ValidationStage.SCORING, result)
        for warning in outcome.warnings:
            updated = updated.with_warning(warning)
        if outcome.success and outcome.execution is not None:
            return updated.with_score_execution(outcome.execution)
        for error in outcome.errors:
            updated = updated.with_error(f"{error.code.value}: {error.message}")
        return updated.with_exit_status(ExitStatus.FAILED)

    def _run_benchmark_stage(self, context: RunContext) -> RunContext:
        outcome = self._benchmark_engine.benchmark(context)
        return self._apply_benchmark_outcome(context, outcome)

    def _apply_benchmark_outcome(
        self,
        context: RunContext,
        outcome: BenchmarkExecutionOutcome,
    ) -> RunContext:
        result = outcome.to_stage_result()
        updated = self._record_stage(context, ValidationStage.BENCHMARK, result)
        for warning in outcome.warnings:
            updated = updated.with_warning(warning)
        if outcome.success and outcome.execution is not None:
            return updated.with_benchmark_execution(outcome.execution)
        for error in outcome.errors:
            updated = updated.with_error(f"{error.code.value}: {error.message}")
        return updated.with_exit_status(ExitStatus.FAILED)

    def _run_certification_stage(self, context: RunContext) -> RunContext:
        outcome = self._certification_engine.certify(context)
        return self._apply_certification_outcome(context, outcome)

    def _apply_certification_outcome(
        self,
        context: RunContext,
        outcome: CertificationExecutionOutcome,
    ) -> RunContext:
        result = outcome.to_stage_result()
        updated = self._record_stage(context, ValidationStage.CERTIFICATION, result)
        for warning in outcome.warnings:
            updated = updated.with_warning(warning)
        if outcome.success and outcome.execution is not None:
            return updated.with_certification_execution(outcome.execution)
        for error in outcome.errors:
            updated = updated.with_error(f"{error.code.value}: {error.message}")
        return updated.with_exit_status(ExitStatus.FAILED)

    def _run_exit(self, context: RunContext) -> RunContext:
        self._inference_runner.shutdown(context)
        exit_status = context.exit_status or ExitStatus.NOT_CERTIFIED
        started = datetime.now(UTC)
        result = PlaceholderStageResult(
            stage=ValidationStage.EXIT,
            status=StageStatus.SUCCEEDED,
            message="pipeline exit",
            data={"exit_status": exit_status.value},
        )
        record = StageRecord(
            stage=ValidationStage.EXIT,
            status=StageStatus.SUCCEEDED,
            started_at=started,
            ended_at=datetime.now(UTC),
            message=result.message,
            result=result,
        )
        return (
            context.with_stage_record(record)
            .with_placeholder_result(result)
            .with_exit_status(exit_status)
            .with_metadata(completed=True)
        )

    def _run_failed_exit(self, context: RunContext) -> RunContext:
        return self._run_exit(context)

    def _run_internal_stage(
        self,
        context: RunContext,
        stage: ValidationStage,
        executor: Callable[[RunContext], PlaceholderStageResult],
    ) -> RunContext:
        return self._record_stage(context, stage, executor(context))

    def _run_port_stage(
        self,
        context: RunContext,
        stage: ValidationStage,
        executor: _StageExecutor,
    ) -> RunContext:
        return self._record_stage(context, stage, executor(context))

    def _record_stage(
        self,
        context: RunContext,
        stage: ValidationStage,
        result: PlaceholderStageResult,
    ) -> RunContext:
        started = datetime.now(UTC)
        if result.stage != stage:
            raise PipelineError(f"Stage {stage.value} returned result for {result.stage.value}.")
        ended = datetime.now(UTC)
        record = StageRecord(
            stage=stage,
            status=result.status,
            started_at=started,
            ended_at=ended,
            message=result.message,
            result=result,
        )
        updated = context.with_stage_record(record).with_placeholder_result(result)
        if result.status == StageStatus.FAILED and stage not in (
            ValidationStage.RESOLVE_ARTIFACTS,
            ValidationStage.RESOLVE_PROFILE,
            ValidationStage.INITIALIZE_INFERENCE,
            ValidationStage.RUN_VALIDATION,
            ValidationStage.SCORING,
            ValidationStage.BENCHMARK,
            ValidationStage.CERTIFICATION,
        ):
            raise PipelineError(f"Stage {stage.value} failed: {result.message}")
        return updated

    def _error_result(
        self,
        context: RunContext,
        exit_status: ExitStatus,
        message: str,
    ) -> ValidationRunResult:
        updated = context.with_error(message).with_exit_status(exit_status)
        return ValidationRunResult(
            exit_status=exit_status,
            run_context=updated,
            message=message,
            completed_at=datetime.now(UTC),
        )
