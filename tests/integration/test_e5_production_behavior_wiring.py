"""Integration tests for Capability Delivery production wiring (E5)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from aiodoo_validation.behavior.capability_pipeline import (
    CapabilityBehaviorPipeline,
    CapabilityPipelineError,
)
from aiodoo_validation.capabilities.bootstrap import create_default_capability_registry
from aiodoo_validation.corpus import (
    EVALUATION_CORPUS_PATH_KEY,
    ConfigurableCorpusProvider,
    CorpusGateError,
    CorpusLoadError,
)
from aiodoo_validation.domain.artifacts import ArtifactBundle, ArtifactDescriptor
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ArtifactType,
    ExecutionTier,
    FingerprintPolicy,
    InferenceLifecycleState,
    ValidationKind,
)
from aiodoo_validation.domain.inference import (
    GenerationMetadata,
    GenerationRequest,
    InferenceGenerationOutcome,
    InferenceInitializationOutcome,
    InferenceResult,
    InferenceSession,
)
from aiodoo_validation.domain.oracle import OracleContext
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.oracles.capability_behavior import (
    build_capability_behavioral_oracle,
    repair_behavior_oracle_id,
)
from aiodoo_validation.production import ProductionPipelineComponents
from aiodoo_validation.profiles.adapter_profile import AdapterProfile

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "capabilities" / "repair"
EVAL_CORPUS = FIXTURES / "eval_corpus"
TRAIN_CORPUS = FIXTURES / "eval_corpus_training"


class _ScriptedInferenceRunner:
    """Deterministic inference for integration tests."""

    def __init__(self, *, texts: dict[str, str] | None = None, fail: bool = False) -> None:
        self._texts = texts or {}
        self._fail = fail

    def initialize(self, context: RunContext) -> InferenceInitializationOutcome:
        session = InferenceSession(
            run_id=context.run_id,
            bundle_digest="digest",
            lifecycle_state=InferenceLifecycleState.READY,
            model_identifier="test",
            adapter_type="repair",
            runtime="test",
        )
        return InferenceInitializationOutcome(
            success=True,
            message="ok",
            session=session,
        )

    def generate(
        self,
        context: RunContext,
        request: GenerationRequest,
    ) -> InferenceGenerationOutcome:
        _ = context
        if self._fail:
            return InferenceGenerationOutcome(success=False, message="forced failure")
        text = self._texts.get(request.prompt, request.prompt)
        return InferenceGenerationOutcome(
            success=True,
            message="ok",
            result=InferenceResult(
                generated_text=text,
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                latency_ms=10,
                memory_usage_mb=1.0,
                metadata=GenerationMetadata(
                    model_identifier="test",
                    adapter_type="repair",
                    seed=None,
                    max_tokens=16,
                    temperature=0.0,
                    runtime="test",
                ),
            ),
        )

    def shutdown(self, context: RunContext) -> None:
        _ = context


def _oracle_context(
    *,
    corpus_path: str | None,
    with_session: bool = True,
) -> OracleContext:
    configuration: dict[str, object] = {}
    if corpus_path is not None:
        configuration[EVALUATION_CORPUS_PATH_KEY] = corpus_path
    session = None
    if with_session:
        session = InferenceSession(
            run_id="run-1",
            bundle_digest="digest",
            lifecycle_state=InferenceLifecycleState.READY,
            model_identifier="test",
            adapter_type="repair",
            runtime="test",
        )
    return OracleContext(
        run_id="run-1",
        profile_name="repair",
        plan_digest="digest",
        protocol_major=1,
        protocol_minor=0,
        execution_tier=ExecutionTier.SMOKE,
        configuration=MappingProxyType(configuration),
        inference_session=session,
    )


class TestConfigurableCorpusProvider:
    def test_missing_path_defers(self) -> None:
        assert ConfigurableCorpusProvider().load(None) is None
        assert ConfigurableCorpusProvider().load("   ") is None

    def test_invalid_path_errors(self) -> None:
        with pytest.raises(CorpusLoadError):
            ConfigurableCorpusProvider().load(EVAL_CORPUS / "missing-dir")

    def test_training_corpus_gate_failure(self) -> None:
        with pytest.raises(CorpusGateError):
            ConfigurableCorpusProvider().load(TRAIN_CORPUS)


class TestCapabilityBehaviorPipeline:
    def test_assemble_eval_corpus(self) -> None:
        loaded = ConfigurableCorpusProvider().load(EVAL_CORPUS)
        assert loaded is not None
        pack = create_default_capability_registry().get("repair")
        assembled = CapabilityBehaviorPipeline().assemble(loaded, pack)
        assert len(assembled.corpus.cases) == 2
        assert assembled.transforms_passed
        assert assembled.corpus.metadata["fingerprint"] == loaded.manifest.fingerprint

    def test_parser_failure(self, tmp_path: Path) -> None:
        records = tmp_path / "records.jsonl"
        records.write_text('{"record_id":"bad"}\n', encoding="utf-8")
        fp = hashlib.sha256(records.read_bytes()).hexdigest()
        (tmp_path / "manifest.json").write_text(
            json.dumps(
                {
                    "corpus_id": "bad",
                    "capability_id": "repair",
                    "role": "evaluation",
                    "dataset_version": "t",
                    "fingerprint": fp,
                }
            ),
            encoding="utf-8",
        )
        loaded = ConfigurableCorpusProvider().load(tmp_path)
        assert loaded is not None
        pack = create_default_capability_registry().get("repair")
        with pytest.raises(CapabilityPipelineError, match="Failed to parse"):
            CapabilityBehaviorPipeline().assemble(loaded, pack)


class TestCapabilityBehavioralOracle:
    def test_missing_corpus_defers(self) -> None:
        runner = _ScriptedInferenceRunner()
        oracle = build_capability_behavioral_oracle(
            capability_id="repair",
            oracle_id=repair_behavior_oracle_id(),
            name="Repair Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=runner,  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=None))
        assert result.success is True
        assert result.metadata["deferred"] is True
        assert "behavioral_deferred" in result.findings

    def test_successful_end_to_end(self) -> None:
        texts = {
            "Use sudo for SQL execute": "Direct SQL should use sudo when intentional.",
            "Already correct": "No edits.",
        }
        runner = _ScriptedInferenceRunner(texts=texts)
        oracle = build_capability_behavioral_oracle(
            capability_id="repair",
            oracle_id=repair_behavior_oracle_id(),
            name="Repair Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=runner,  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=str(EVAL_CORPUS)))
        assert result.metadata["deferred"] is False
        assert result.metadata["transforms_passed"] is True
        assert result.metadata["case_count"] == 2
        assert result.success is True
        assert result.metadata["validation_kind"] == ValidationKind.BEHAVIORAL.value

    def test_gate_failure(self) -> None:
        runner = _ScriptedInferenceRunner()
        oracle = build_capability_behavioral_oracle(
            capability_id="repair",
            oracle_id=repair_behavior_oracle_id(),
            name="Repair Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=runner,  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=str(TRAIN_CORPUS)))
        assert result.success is False
        assert "corpus_error" in result.findings

    def test_runner_failure(self) -> None:
        runner = _ScriptedInferenceRunner(fail=True)
        oracle = build_capability_behavioral_oracle(
            capability_id="repair",
            oracle_id=repair_behavior_oracle_id(),
            name="Repair Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=runner,  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=str(EVAL_CORPUS)))
        assert result.metadata["transforms_passed"] is True
        assert result.success is False
        assert result.metadata["fail_count"] == 2


class TestProductionWiring:
    def test_repair_behavior_oracle_registered(self) -> None:
        components = ProductionPipelineComponents.create()
        assert components.oracle_runner.registry.contains(repair_behavior_oracle_id())

    def test_repair_plan_includes_behavior_stage(self) -> None:
        profile = AdapterProfile.create("repair", odoo_versions=(18,))
        request = ValidationRequest(
            profile_name="repair",
            base_model_ref="./base",
            adapter_ref="./adapter",
            metadata={EVALUATION_CORPUS_PATH_KEY: str(EVAL_CORPUS)},
        )
        context = RunContext.begin(request)
        bundle = ArtifactBundle(
            base_model=ArtifactDescriptor(
                artifact_type=ArtifactType.BASE_MODEL,
                logical_ref="base",
                location_digest="x",
                metadata={"identifier": "qwen"},
            ),
            adapter=ArtifactDescriptor(
                artifact_type=ArtifactType.CODING_ADAPTER,
                logical_ref="adapter",
                location_digest="y",
                metadata={"adapter_type": "repair"},
            ),
            merged_model=None,
            protocol_major=1,
            protocol_minor=0,
            fingerprint_policy=FingerprintPolicy.OFF,
            bundle_digest="d1",
        )
        plan = profile.build_validation_plan(bundle=bundle, context=context)
        ids = [stage.stage_id for stage in plan.oracle_pipeline]
        assert repair_behavior_oracle_id() in ids
        assert plan.configuration.get(EVALUATION_CORPUS_PATH_KEY) == str(EVAL_CORPUS)

    def test_production_does_not_import_repair_parser_directly(self) -> None:
        import inspect

        import aiodoo_validation.production as production_mod

        source = inspect.getsource(production_mod)
        assert "RepairRecordParser" not in source
        assert "create_default_capability_registry" in source
