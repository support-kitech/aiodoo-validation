"""Integration tests for Evaluation behavioral production wiring (Phase 2)."""

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
from aiodoo_validation.certification.behavioral import BehaviorGatedCertificationPolicy
from aiodoo_validation.certification.ids import EVALUATION_CERTIFICATION_BEHAVIOR
from aiodoo_validation.corpus import (
    EVALUATION_CORPUS_PATH_KEY,
    EVALUATION_EVAL_FIXTURE_CORPUS_ID,
    ConfigurableCorpusProvider,
    CorpusLoadError,
    builtin_corpus_pin_registry,
)
from aiodoo_validation.corpus.catalog import EVALUATION_CORPUS_ID_KEY
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
    evaluation_behavior_oracle_id,
)
from aiodoo_validation.production import ProductionPipelineComponents
from aiodoo_validation.profiles.adapter_profile import AdapterProfile
from aiodoo_validation.reporting.production import default_production_report_templates
from aiodoo_validation.scoring.behavioral import BehavioralEvidenceScorePolicy
from aiodoo_validation.scoring.ids import EVALUATION_SCORE_BEHAVIOR

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "capabilities" / "evaluation"
EVAL_CORPUS = FIXTURES / "eval_corpus"


class _ScriptedInferenceRunner:
    """Deterministic inference for evaluation behavior integration tests."""

    def __init__(self, *, texts: dict[str, str] | None = None, fail: bool = False) -> None:
        self._texts = texts or {}
        self._fail = fail

    def initialize(self, context: RunContext) -> InferenceInitializationOutcome:
        session = InferenceSession(
            run_id=context.run_id,
            bundle_digest="digest",
            lifecycle_state=InferenceLifecycleState.READY,
            model_identifier="test",
            adapter_type="evaluation",
            runtime="test",
        )
        return InferenceInitializationOutcome(success=True, message="ok", session=session)

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
                    adapter_type="evaluation",
                    seed=None,
                    max_tokens=16,
                    temperature=0.0,
                    runtime="test",
                ),
            ),
        )

    def shutdown(self, context: RunContext) -> None:
        _ = context


def _bundle() -> ArtifactBundle:
    return ArtifactBundle(
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
            metadata={"adapter_type": "evaluation"},
        ),
        merged_model=None,
        protocol_major=1,
        protocol_minor=0,
        fingerprint_policy=FingerprintPolicy.OFF,
        bundle_digest="digest",
    )


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
            run_id="run-evaluation",
            bundle_digest="digest",
            lifecycle_state=InferenceLifecycleState.READY,
            model_identifier="test",
            adapter_type="evaluation",
            runtime="test",
        )
    return OracleContext(
        run_id="run-evaluation",
        profile_name="evaluation",
        plan_digest="digest",
        protocol_major=1,
        protocol_minor=0,
        execution_tier=ExecutionTier.SMOKE,
        configuration=MappingProxyType(configuration),
        inference_session=session,
        artifact_bundle=_bundle(),
    )


class TestEvaluationCorpusProvider:
    def test_missing_path_defers(self) -> None:
        assert ConfigurableCorpusProvider().load(None) is None
        assert ConfigurableCorpusProvider().load("   ") is None

    def test_invalid_path_errors(self) -> None:
        with pytest.raises(CorpusLoadError):
            ConfigurableCorpusProvider().load(EVAL_CORPUS / "missing-dir")


class TestEvaluationCapabilityBehaviorPipeline:
    def test_assemble_eval_corpus(self) -> None:
        loaded = ConfigurableCorpusProvider().load(EVAL_CORPUS)
        assert loaded is not None
        pack = create_default_capability_registry().get("evaluation")
        assembled = CapabilityBehaviorPipeline().assemble(loaded, pack)
        assert len(assembled.corpus.cases) == 2
        assert assembled.transforms_passed is True
        assert assembled.corpus.metadata["fingerprint"] == loaded.manifest.fingerprint

    def test_parser_failure(self, tmp_path: Path) -> None:
        records = tmp_path / "records.jsonl"
        records.write_text('{"record_id":"bad"}\n', encoding="utf-8")
        fp = hashlib.sha256(records.read_bytes()).hexdigest()
        (tmp_path / "manifest.json").write_text(
            json.dumps(
                {
                    "corpus_id": "bad",
                    "capability_id": "evaluation",
                    "role": "evaluation",
                    "dataset_version": "t",
                    "fingerprint": fp,
                }
            ),
            encoding="utf-8",
        )
        loaded = ConfigurableCorpusProvider().load(tmp_path)
        assert loaded is not None
        pack = create_default_capability_registry().get("evaluation")
        with pytest.raises(CapabilityPipelineError, match="Failed to parse"):
            CapabilityBehaviorPipeline().assemble(loaded, pack)

    def test_capability_mismatch_errors(self, tmp_path: Path) -> None:
        records = tmp_path / "records.jsonl"
        records.write_text("{}\n", encoding="utf-8")
        fp = hashlib.sha256(records.read_bytes()).hexdigest()
        (tmp_path / "manifest.json").write_text(
            json.dumps(
                {
                    "corpus_id": "wrong-cap",
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
        pack = create_default_capability_registry().get("evaluation")
        with pytest.raises(CapabilityPipelineError, match="does not match"):
            CapabilityBehaviorPipeline().assemble(loaded, pack)


class TestEvaluationBehaviorOracle:
    def test_missing_corpus_defers(self) -> None:
        oracle = build_capability_behavioral_oracle(
            capability_id="evaluation",
            oracle_id=evaluation_behavior_oracle_id(),
            name="Evaluation Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=_ScriptedInferenceRunner(),  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=None))
        assert result.success is True
        assert result.metadata["deferred"] is True
        assert "behavioral_deferred" in result.findings
        assert result.metadata["validation_kind"] == ValidationKind.BEHAVIORAL.value

    def test_successful_end_to_end(self) -> None:
        texts = {
            "Rename the reply template label.": "Update reply template label.",
            "Add evaluation turn helper.": (
                "class EvaluationTurn:\n"
                "    def __init__(self, text):\n"
                "        self.text = text\n\n"
                "    def is_user_turn(self):\n"
                "        return bool(self.text)\n"
            ),
        }
        oracle = build_capability_behavioral_oracle(
            capability_id="evaluation",
            oracle_id=evaluation_behavior_oracle_id(),
            name="Evaluation Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=_ScriptedInferenceRunner(texts=texts),  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=str(EVAL_CORPUS)))
        assert result.metadata["deferred"] is False
        assert result.metadata["transforms_passed"] is True
        assert result.metadata["capability_id"] == "evaluation"
        assert result.metadata["case_count"] == 2
        assert result.success is True
        assert result.metadata["validation_kind"] == ValidationKind.BEHAVIORAL.value

    def test_incorrect_outputs_fail(self) -> None:
        oracle = build_capability_behavioral_oracle(
            capability_id="evaluation",
            oracle_id=evaluation_behavior_oracle_id(),
            name="Evaluation Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=_ScriptedInferenceRunner(
                texts={
                    "Rename the reply template label.": "wrong",
                    "Add evaluation turn helper.": "also wrong",
                }
            ),  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=str(EVAL_CORPUS)))
        assert result.metadata["transforms_passed"] is True
        assert result.success is False
        assert result.metadata["fail_count"] == 2

    def test_runner_failure(self) -> None:
        oracle = build_capability_behavioral_oracle(
            capability_id="evaluation",
            oracle_id=evaluation_behavior_oracle_id(),
            name="Evaluation Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=_ScriptedInferenceRunner(fail=True),  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=str(EVAL_CORPUS)))
        assert result.metadata["transforms_passed"] is True
        assert result.success is False
        assert result.metadata["fail_count"] == 2

    def test_invalid_corpus_path(self) -> None:
        oracle = build_capability_behavioral_oracle(
            capability_id="evaluation",
            oracle_id=evaluation_behavior_oracle_id(),
            name="Evaluation Behavior",
            description="test",
            capability_registry=create_default_capability_registry(),
            inference_runner=_ScriptedInferenceRunner(),  # type: ignore[arg-type]
        )
        result = oracle.execute(_oracle_context(corpus_path=str(EVAL_CORPUS / "missing")))
        assert result.success is False
        assert "corpus_error" in result.findings


class TestEvaluationCorpusPin:
    def test_builtin_pin_resolves_evaluation_fixture(self) -> None:
        registry = builtin_corpus_pin_registry()
        pin = registry.get(EVALUATION_EVAL_FIXTURE_CORPUS_ID)
        assert pin.capability_id == "evaluation"
        assert registry.get("evaluation.eval").corpus_id == EVALUATION_EVAL_FIXTURE_CORPUS_ID


class TestEvaluationPlanCorpusResolution:
    def test_plan_includes_resolved_corpus_path(self) -> None:
        profile = AdapterProfile.create("evaluation", odoo_versions=(18,))
        request = ValidationRequest(
            profile_name="evaluation",
            base_model_ref="base",
            adapter_ref="adapter",
            execution_tier=ExecutionTier.SMOKE,
            metadata={EVALUATION_CORPUS_ID_KEY: "evaluation.eval"},
        )
        context = RunContext.begin(request).with_artifact_bundle(_bundle())
        plan = profile.build_validation_plan(bundle=_bundle(), context=context)
        assert plan.configuration.get(EVALUATION_CORPUS_ID_KEY) == EVALUATION_EVAL_FIXTURE_CORPUS_ID
        assert EVALUATION_CORPUS_PATH_KEY in plan.configuration
        oracle_ids = {s.stage_id for s in plan.oracle_pipeline}
        assert "evaluation.oracle.behavior.evaluation" in oracle_ids


class TestEvaluationScoreCertReportFactories:
    def test_create_for_evaluation_factories(self) -> None:
        score = BehavioralEvidenceScorePolicy.create_for_evaluation()
        assert score.metadata.policy_id == EVALUATION_SCORE_BEHAVIOR
        assert score.metadata.supported_profile == "evaluation"
        cert = BehaviorGatedCertificationPolicy.create_for_evaluation()
        assert cert.metadata.policy_id == EVALUATION_CERTIFICATION_BEHAVIOR
        assert cert.metadata.supported_profile == "evaluation"
        assert cert.source_score_policy_id == EVALUATION_SCORE_BEHAVIOR
        reports = default_production_report_templates(profile="evaluation")
        assert any(t.metadata.template_id == "evaluation.report.behavior" for t in reports)


class TestProductionEvaluationRegistration:
    def test_production_registers_evaluation_behavior_oracle(self) -> None:
        components = ProductionPipelineComponents.create()
        registry = components.oracle_runner.registry
        assert registry.contains("evaluation.oracle.behavior.evaluation")
        assert registry.contains("repair.oracle.behavior.repair")
        assert registry.contains("coding.oracle.behavior.coding")
        assert registry.contains("planner.oracle.behavior.planner")
        assert registry.contains("conversation.oracle.behavior.conversation")
        assert registry.contains("execution.oracle.behavior.execution")
        assert registry.contains("approval.oracle.behavior.approval")
        assert registry.contains("evaluation.oracle.behavior.evaluation")

    def test_production_does_not_import_evaluation_parser_directly(self) -> None:
        import inspect

        import aiodoo_validation.production as production_mod

        source = inspect.getsource(production_mod)
        assert "EvaluationRecordParser" not in source
        assert "create_default_capability_registry" in source
