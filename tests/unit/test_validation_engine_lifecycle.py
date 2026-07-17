"""Integration tests for ValidationEngine lifecycle."""

import pytest

from aiodoo_validation.domain.enums import (
    ExecutionTier,
    ExitStatus,
    StageStatus,
    SupportedValidationProfile,
    ValidationStage,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import PIPELINE_STAGE_ORDER, ValidationEngine
from aiodoo_validation.exceptions import InvalidRequestError

STUB_PORT_STAGES = (
    ValidationStage.RESOLVE_ARTIFACTS,
    ValidationStage.RESOLVE_PROFILE,
    ValidationStage.INITIALIZE_INFERENCE,
    ValidationStage.RUN_VALIDATION,
    ValidationStage.SCORING,
    ValidationStage.BENCHMARK,
    ValidationStage.CERTIFICATION,
    ValidationStage.REPORT,
)


def _sample_request() -> ValidationRequest:
    return ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref="Qwen/Qwen3-8B",
        adapter_ref="artifacts/adapters/EXP-0001/stub",
        execution_tier=ExecutionTier.FULL,
        run_id="lifecycle-run-1",
    )


def test_pipeline_stage_order_matches_tdd() -> None:
    assert PIPELINE_STAGE_ORDER == (
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


def test_stub_engine_runs_complete_lifecycle() -> None:
    engine = ValidationEngine.with_stubs()
    result = engine.run(_sample_request())

    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.run_id == "lifecycle-run-1"
    assert len(result.run_context.stage_records) == len(PIPELINE_STAGE_ORDER)

    executed_stages = tuple(record.stage for record in result.run_context.stage_records)
    assert executed_stages == PIPELINE_STAGE_ORDER

    for record in result.run_context.stage_records:
        assert record.status is StageStatus.SUCCEEDED
        assert record.result is not None

    for stage in STUB_PORT_STAGES:
        if stage is ValidationStage.RESOLVE_ARTIFACTS:
            continue
        assert result.run_context.placeholder_results[stage].data.get("stub") is True

    artifact_result = result.run_context.placeholder_results[ValidationStage.RESOLVE_ARTIFACTS]
    assert artifact_result.status is StageStatus.SUCCEEDED
    assert result.run_context.artifact_bundle is not None
    assert result.run_context.artifact_bundle.base_model.artifact_type.value == "base_model"

    for stage in PIPELINE_STAGE_ORDER:
        assert stage in result.run_context.placeholder_results


def test_invalid_profile_rejected_at_request_construction() -> None:
    with pytest.raises(InvalidRequestError):
        ValidationRequest(
            profile_name="planner",
            base_model_ref="base",
            adapter_ref="adapter",
        )
