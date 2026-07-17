"""Unit tests for Phase 3 inference runner."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aiodoo_validation.domain.artifacts import (
    ArtifactBundle,
    ArtifactDescriptor,
    ArtifactFingerprint,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ArtifactType,
    ExecutionTier,
    ExitStatus,
    FingerprintPolicy,
    InferenceErrorCode,
    InferenceLifecycleState,
    StageStatus,
    SupportedValidationProfile,
    ValidationStage,
)
from aiodoo_validation.domain.inference import GenerationRequest, InferenceError
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.inference.compatibility import validate_inference_artifacts
from aiodoo_validation.inference.paths import ARTIFACT_PATHS_KEY, build_artifact_paths_metadata
from aiodoo_validation.inference.runner import RealInferenceRunner
from aiodoo_validation.inference.runtime.mock import MockModelRuntime
from aiodoo_validation.inference.runtime.port import LoadedModelHandle
from aiodoo_validation.inference.stub_runner import StubInferenceRunner
from aiodoo_validation.resolution.filesystem import FilesystemArtifactResolver
from aiodoo_validation.stubs import StubPipelineComponents

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def _request(*, base: str, adapter: str) -> ValidationRequest:
    return ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref=base,
        adapter_ref=adapter,
        execution_tier=ExecutionTier.STANDARD,
        run_id="inference-test",
    )


def _context(request: ValidationRequest) -> RunContext:
    return RunContext.begin(request)


def _bundle_with_paths(*, base: str, adapter: str) -> ArtifactBundle:
    fp = ArtifactFingerprint(value="placeholder:test", placeholder=True)
    base_desc = ArtifactDescriptor(
        artifact_type=ArtifactType.BASE_MODEL,
        logical_ref="base_model",
        location_digest=fp.value,
        metadata={
            "model_family": "qwen",
            "identifier": "qwen3-8b",
        },
        fingerprint=fp,
    )
    adapter_desc = ArtifactDescriptor(
        artifact_type=ArtifactType.CODING_ADAPTER,
        logical_ref="adapter",
        location_digest="placeholder:adapter",
        metadata={"adapter_type": "coding"},
        fingerprint=ArtifactFingerprint(value="placeholder:adapter", placeholder=True),
    )
    return ArtifactBundle(
        base_model=base_desc,
        adapter=adapter_desc,
        merged_model=None,
        protocol_major=1,
        protocol_minor=0,
        fingerprint_policy=FingerprintPolicy.OFF,
        bundle_digest="bundle-test",
        metadata={
            ARTIFACT_PATHS_KEY: build_artifact_paths_metadata(
                base_model=base,
                adapter=adapter,
            )
        },
    )


def test_mock_runtime_load_generate_unload_lifecycle() -> None:
    runtime = MockModelRuntime()
    bundle = _bundle_with_paths(base="/tmp/base", adapter="/tmp/adapter")
    handle = runtime.load(bundle, paths=MagicMock())
    runtime.verify(handle)
    result = runtime.generate(
        handle,
        GenerationRequest(prompt="Write Odoo model code", max_tokens=16, temperature=0.0, seed=7),
    )
    runtime.unload(handle)

    assert result.generated_text.startswith("[mock:")
    assert result.prompt_tokens >= 1
    assert result.completion_tokens >= 1
    assert result.memory_usage_mb == 128.0
    assert result.metadata.runtime == "mock"


def test_real_inference_runner_initialize_and_generate() -> None:
    request = _request(base=str(FIXTURES / "base_model"), adapter=str(FIXTURES / "coding_adapter"))
    resolver = FilesystemArtifactResolver.create_default()
    resolved = resolver.resolve(_context(request))
    assert resolved.success and resolved.bundle is not None

    context = _context(request).with_artifact_bundle(resolved.bundle)
    runner = RealInferenceRunner(runtime=MockModelRuntime())
    init_outcome = runner.initialize(context)
    assert init_outcome.success is True
    assert init_outcome.session is not None
    assert init_outcome.session.lifecycle_state is InferenceLifecycleState.READY

    gen_outcome = runner.generate(
        context,
        GenerationRequest(prompt="hello", max_tokens=8, temperature=0.1, seed=1),
    )
    assert gen_outcome.success is True
    assert gen_outcome.result is not None
    assert gen_outcome.result.total_tokens > 0

    runner.shutdown(context)


def test_missing_bundle_fails_gracefully() -> None:
    runner = RealInferenceRunner(runtime=MockModelRuntime())
    outcome = runner.initialize(_context(_request(base="a", adapter="b")))

    assert outcome.success is False
    assert outcome.errors[0].code is InferenceErrorCode.MISSING_BUNDLE


def test_unsupported_planner_adapter_rejected() -> None:
    bundle = _bundle_with_paths(base="/tmp/base", adapter="/tmp/adapter")
    fp = ArtifactFingerprint(value="placeholder:adapter", placeholder=True)
    planner_adapter = ArtifactDescriptor(
        artifact_type=ArtifactType.CODING_ADAPTER,
        logical_ref="adapter",
        location_digest=fp.value,
        metadata={"adapter_type": "planner"},
        fingerprint=fp,
    )
    bundle = ArtifactBundle(
        base_model=bundle.base_model,
        adapter=planner_adapter,
        merged_model=None,
        protocol_major=1,
        protocol_minor=0,
        fingerprint_policy=FingerprintPolicy.OFF,
        bundle_digest="bundle-planner",
        metadata=bundle.metadata,
    )
    errors = validate_inference_artifacts(bundle)
    assert any(error.code is InferenceErrorCode.UNSUPPORTED_ADAPTER for error in errors)


def test_generation_requires_initialization() -> None:
    runner = RealInferenceRunner(runtime=MockModelRuntime())
    context = _context(_request(base="a", adapter="b")).with_artifact_bundle(
        _bundle_with_paths(base="a", adapter="b")
    )
    outcome = runner.generate(context, GenerationRequest(prompt="test", max_tokens=8))
    assert outcome.success is False
    assert outcome.errors[0].code is InferenceErrorCode.NOT_INITIALIZED


def test_generation_empty_prompt_rejected() -> None:
    runner = RealInferenceRunner(runtime=MockModelRuntime())
    context = _context(_request(base="a", adapter="b")).with_artifact_bundle(
        _bundle_with_paths(base="a", adapter="b")
    )
    runner.initialize(context)
    outcome = runner.generate(context, GenerationRequest(prompt="   ", max_tokens=8))
    assert outcome.success is False
    assert outcome.errors[0].code is InferenceErrorCode.UNSUPPORTED_CONFIG


def test_runtime_load_failure_structured() -> None:
    runtime = MagicMock()
    runtime.runtime_name = "mock-fail"
    runtime.load.side_effect = InferenceError(
        code=InferenceErrorCode.MODEL_LOAD_FAILURE,
        message="load failed",
    )
    runner = RealInferenceRunner(runtime=runtime)
    context = _context(_request(base="a", adapter="b")).with_artifact_bundle(
        _bundle_with_paths(base="a", adapter="b")
    )
    outcome = runner.initialize(context)
    assert outcome.success is False
    assert outcome.errors[0].code is InferenceErrorCode.MODEL_LOAD_FAILURE


def test_stub_inference_runner_default_ci() -> None:
    runner = StubInferenceRunner.create()
    request = _request(base="stub/base", adapter="stub/adapter")
    context = RunContext.begin(request)
    outcome = runner.initialize(context)
    assert outcome.success is True
    assert outcome.session is not None
    assert outcome.session.runtime == "stub"


def test_engine_mock_inference_lifecycle() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    result = ValidationEngine.with_mock_inference().run(request)

    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.inference_session is not None
    inference_stage = result.run_context.placeholder_results[ValidationStage.INITIALIZE_INFERENCE]
    assert inference_stage.status is StageStatus.SUCCEEDED


def test_engine_inference_failure_does_not_crash() -> None:
    failing_runtime = MagicMock()
    failing_runtime.runtime_name = "fail"
    failing_runtime.load.side_effect = InferenceError(
        code=InferenceErrorCode.OOM,
        message="CUDA OOM",
    )
    components = StubPipelineComponents.create()
    engine = ValidationEngine(
        artifact_resolver=FilesystemArtifactResolver.create_default(),
        profile_engine=components.profile_engine,
        inference_runner=RealInferenceRunner(runtime=failing_runtime),
        validation_runner=components.validation_runner,
        scoring_engine=components.scoring_engine,
        benchmark_engine=components.benchmark_engine,
        certification_engine=components.certification_engine,
        report_generator=components.report_generator,
    )
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    result = engine.run(request)

    assert result.exit_status is ExitStatus.FAILED
    assert result.run_context.inference_session is None
    assert ValidationStage.RUN_VALIDATION not in {
        record.stage for record in result.run_context.stage_records
    }


def test_inference_result_immutable() -> None:
    runtime = MockModelRuntime()
    bundle = _bundle_with_paths(base="/tmp/base", adapter="/tmp/adapter")
    handle = runtime.load(bundle, paths=MagicMock())
    result = runtime.generate(handle, GenerationRequest(prompt="x", max_tokens=4))
    with pytest.raises(FrozenInstanceError):
        result.generated_text = "changed"  # type: ignore[misc]
    runtime.unload(handle)


def test_resource_cleanup_after_shutdown() -> None:
    runtime = MockModelRuntime()
    runner = RealInferenceRunner(runtime=runtime)
    context = _context(_request(base="a", adapter="b")).with_artifact_bundle(
        _bundle_with_paths(base="a", adapter="b")
    )
    runner.initialize(context)
    runner.shutdown(context)
    outcome = runner.generate(context, GenerationRequest(prompt="after shutdown", max_tokens=4))
    assert outcome.errors[0].code is InferenceErrorCode.NOT_INITIALIZED


def test_qwen_runtime_missing_dependencies() -> None:
    from aiodoo_validation.inference.runtime.qwen import QwenModelRuntime

    runtime = QwenModelRuntime()
    bundle = _bundle_with_paths(base="/tmp/base", adapter="/tmp/adapter")
    with pytest.raises(InferenceError) as exc_info:
        runtime.load(bundle, paths=MagicMock())
    assert exc_info.value.code in {
        InferenceErrorCode.UNSUPPORTED_CONFIG,
        InferenceErrorCode.MODEL_LOAD_FAILURE,
        InferenceErrorCode.ADAPTER_LOAD_FAILURE,
    }


def test_loaded_model_handle_opaque() -> None:
    handle = LoadedModelHandle(token="abc", model_identifier="qwen3-8b", adapter_type="coding")
    assert "path" not in repr(handle)
