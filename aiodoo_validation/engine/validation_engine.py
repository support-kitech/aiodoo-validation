"""Validation Engine — orchestrates the frozen TDD lifecycle."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ExitStatus, StageStatus, ValidationStage
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.result import ValidationRunResult
from aiodoo_validation.domain.stage import PlaceholderStageResult, StageRecord
from aiodoo_validation.engine.protocol import negotiate_protocol
from aiodoo_validation.exceptions import (
    AiodooValidationError,
    InvalidRequestError,
    PipelineError,
    ProtocolError,
)
from aiodoo_validation.ports import (
    ArtifactResolverPort,
    BenchmarkEnginePort,
    CertificationEnginePort,
    InferenceRunnerPort,
    ProfileEnginePort,
    ReportGeneratorPort,
    ScoringEnginePort,
    ValidationRunnerPort,
)
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

    Executes the complete lifecycle using injected ports. Phase 0/1 ships with
    stub implementations only.
    """

    def __init__(
        self,
        *,
        artifact_resolver: ArtifactResolverPort,
        profile_engine: ProfileEnginePort,
        inference_runner: InferenceRunnerPort,
        validation_runner: ValidationRunnerPort,
        scoring_engine: ScoringEnginePort,
        benchmark_engine: BenchmarkEnginePort,
        certification_engine: CertificationEnginePort,
        report_generator: ReportGeneratorPort,
    ) -> None:
        self._artifact_resolver = artifact_resolver
        self._profile_engine = profile_engine
        self._inference_runner = inference_runner
        self._validation_runner = validation_runner
        self._scoring_engine = scoring_engine
        self._benchmark_engine = benchmark_engine
        self._certification_engine = certification_engine
        self._report_generator = report_generator

    @classmethod
    def with_stubs(cls) -> ValidationEngine:
        """Construct an engine wired with Phase 0/1 stub ports."""
        stubs = StubPipelineComponents.create()
        return cls(
            artifact_resolver=stubs.artifact_resolver,
            profile_engine=stubs.profile_engine,
            inference_runner=stubs.inference_runner,
            validation_runner=stubs.validation_runner,
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
            return ValidationRunResult(
                exit_status=exit_status,
                run_context=context,
                message="Validation lifecycle completed (stub pipeline).",
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
                context = self._run_port_stage(context, stage, self._artifact_resolver.resolve)
            elif stage == ValidationStage.RESOLVE_PROFILE:
                context = self._run_port_stage(context, stage, self._profile_engine.resolve_profile)
            elif stage == ValidationStage.INITIALIZE_INFERENCE:
                context = self._run_port_stage(context, stage, self._inference_runner.initialize)
            elif stage == ValidationStage.RUN_VALIDATION:
                context = self._run_port_stage(
                    context, stage, self._validation_runner.run_validation
                )
            elif stage == ValidationStage.SCORING:
                context = self._run_port_stage(context, stage, self._scoring_engine.score)
            elif stage == ValidationStage.BENCHMARK:
                context = self._run_port_stage(context, stage, self._benchmark_engine.benchmark)
            elif stage == ValidationStage.CERTIFICATION:
                context = self._run_port_stage(context, stage, self._certification_engine.certify)
            elif stage == ValidationStage.REPORT:
                context = self._run_port_stage(
                    context, stage, self._report_generator.generate_report
                )
            elif stage == ValidationStage.EXIT:
                context = self._run_exit(context)
        return context

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

    def _run_exit(self, context: RunContext) -> RunContext:
        started = datetime.now(UTC)
        result = PlaceholderStageResult(
            stage=ValidationStage.EXIT,
            status=StageStatus.SUCCEEDED,
            message="pipeline exit",
            data={"exit_status": ExitStatus.NOT_CERTIFIED.value},
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
            .with_exit_status(ExitStatus.NOT_CERTIFIED)
            .with_metadata(completed=True)
        )

    def _run_internal_stage(
        self,
        context: RunContext,
        stage: ValidationStage,
        executor: Callable[[RunContext], PlaceholderStageResult],
    ) -> RunContext:
        return self._run_stage(context, stage, executor(context))

    def _run_port_stage(
        self,
        context: RunContext,
        stage: ValidationStage,
        executor: _StageExecutor,
    ) -> RunContext:
        return self._run_stage(context, stage, executor(context))

    def _run_stage(
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
        if result.status == StageStatus.FAILED:
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
