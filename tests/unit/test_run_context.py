"""Unit tests for RunContext."""

from datetime import UTC, datetime

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ExecutionTier,
    ExitStatus,
    StageStatus,
    SupportedValidationProfile,
    ValidationStage,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.stage import PlaceholderStageResult, StageRecord


def _sample_request() -> ValidationRequest:
    return ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref="Qwen/Qwen3-8B",
        adapter_ref="artifacts/adapters/aiodoo-coding/stub",
        execution_tier=ExecutionTier.STANDARD,
        run_id="run-test-001",
    )


def test_run_context_begin_uses_request_run_id() -> None:
    context = RunContext.begin(_sample_request())
    assert context.run_id == "run-test-001"
    assert context.execution_tier is ExecutionTier.STANDARD
    assert context.current_stage is ValidationStage.LOAD_REQUEST


def test_run_context_generates_run_id_when_missing() -> None:
    request = ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref="base",
        adapter_ref="adapter",
    )
    context = RunContext.begin(request)
    assert context.run_id.startswith("run-")


def test_run_context_immutable_updates() -> None:
    context = RunContext.begin(_sample_request())
    updated = context.with_warning("warn-1").with_error("err-1")
    assert context.warnings == ()
    assert updated.warnings == ("warn-1",)
    assert updated.errors == ("err-1",)

    now = datetime.now(UTC)
    record = StageRecord(
        stage=ValidationStage.LOAD_REQUEST,
        status=StageStatus.SUCCEEDED,
        started_at=now,
        ended_at=now,
        message="ok",
    )
    with_record = updated.with_stage_record(record)
    assert with_record.stage_status(ValidationStage.LOAD_REQUEST) is StageStatus.SUCCEEDED

    placeholder = PlaceholderStageResult(
        stage=ValidationStage.REPORT,
        status=StageStatus.SUCCEEDED,
        message="stub",
    )
    with_placeholder = with_record.with_placeholder_result(placeholder)
    assert with_placeholder.placeholder_results[ValidationStage.REPORT] is placeholder

    with_exit = with_placeholder.with_exit_status(ExitStatus.NOT_CERTIFIED)
    assert with_exit.exit_status is ExitStatus.NOT_CERTIFIED
