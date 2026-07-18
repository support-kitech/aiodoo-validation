"""Unit tests for behavioral validation and comparator architecture."""

from __future__ import annotations

from aiodoo_validation.behavior import BehaviorRunner
from aiodoo_validation.comparators import (
    ComparatorRegistry,
    ExactMatchComparator,
    NormalizedTextComparator,
)
from aiodoo_validation.domain.behavior import (
    BehaviorCase,
    BehaviorCorpus,
    BehaviorPrompt,
    ExpectedOutput,
    GeneratedOutput,
    empty_behavior_corpus,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ComparatorKind,
    ExecutionTier,
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
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.execution import (
    allows_certification,
    behavior_case_limit,
    is_framework_only_tier,
    normalize_execution_tier,
    requires_real_inference,
)
from aiodoo_validation.oracles.behavioral import (
    BehavioralOracle,
    behavioral_oracle_metadata,
    build_deferred_behavioral_oracles,
)


class _FixedInferenceRunner:
    def __init__(self, text: str) -> None:
        self._text = text

    def initialize(self, context: RunContext) -> InferenceInitializationOutcome:
        session = InferenceSession(
            run_id=context.run_id,
            bundle_digest="digest",
            lifecycle_state=InferenceLifecycleState.READY,
            model_identifier="test",
            adapter_type="coding",
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
        _ = context, request
        return InferenceGenerationOutcome(
            success=True,
            message="ok",
            result=InferenceResult(
                generated_text=self._text,
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                latency_ms=10,
                memory_usage_mb=1.5,
                metadata=GenerationMetadata(
                    model_identifier="test",
                    adapter_type="coding",
                    seed=None,
                    max_tokens=16,
                    temperature=0.0,
                    runtime="test",
                ),
            ),
        )

    def shutdown(self, context: RunContext) -> None:
        _ = context


def _context(tier: ExecutionTier = ExecutionTier.SMOKE) -> RunContext:
    return RunContext.begin(
        ValidationRequest(
            profile_name="coding",
            base_model_ref="base",
            adapter_ref="adapter",
            execution_tier=tier,
        )
    )


def test_exact_and_normalized_comparators() -> None:
    expected = ExpectedOutput(text="hello world")
    generated = GeneratedOutput(text="hello world")
    assert ExactMatchComparator().compare(expected=expected, generated=generated).passed
    spaced = GeneratedOutput(text="  hello   world  ")
    assert not ExactMatchComparator().compare(expected=expected, generated=spaced).passed
    assert NormalizedTextComparator().compare(expected=expected, generated=spaced).passed


def test_comparator_registry_includes_deferred_kinds() -> None:
    registry = ComparatorRegistry.create_default()
    deferred = registry.get(ComparatorKind.SEMANTIC)
    result = deferred.compare(
        expected=ExpectedOutput(text="a"),
        generated=GeneratedOutput(text="a"),
    )
    assert result.passed is False
    assert "not implemented" in result.message
    assert registry.get(ComparatorKind.AST).metadata.capabilities.implemented is True
    assert registry.get(ComparatorKind.XML).metadata.capabilities.implemented is True
    assert registry.get(ComparatorKind.JSON).metadata.capabilities.implemented is True
    assert registry.get(ComparatorKind.TOKEN_SIMILARITY).metadata.capabilities.implemented is True


def test_behavior_runner_defers_empty_corpus() -> None:
    suite = BehaviorRunner.create_default().run_suite(
        context=_context(),
        corpus=empty_behavior_corpus(profile_name="coding"),
        inference_runner=_FixedInferenceRunner("x"),
    )
    assert suite.deferred is True
    assert suite.case_count == 0


def test_behavior_runner_evaluates_cases() -> None:
    corpus = BehaviorCorpus(
        corpus_id="coding.behavior.test",
        profile_name="coding",
        cases=(
            BehaviorCase(
                case_id="case-1",
                prompt=BehaviorPrompt(text="say hi"),
                expected=ExpectedOutput(text="hello"),
                comparator_kind=ComparatorKind.EXACT,
            ),
        ),
    )
    suite = BehaviorRunner.create_default().run_suite(
        context=_context(ExecutionTier.SMOKE),
        corpus=corpus,
        inference_runner=_FixedInferenceRunner("hello"),
    )
    assert suite.deferred is False
    assert suite.all_passed is True
    assert suite.results[0].generated is not None
    assert suite.results[0].generated.latency_ms == 10


def test_behavior_case_limit_by_tier() -> None:
    assert behavior_case_limit(ExecutionTier.STANDARD) == 0
    assert behavior_case_limit(ExecutionTier.SMOKE) == 8
    assert behavior_case_limit(ExecutionTier.FULL) is None
    assert behavior_case_limit("prod") is None


def test_execution_tier_helpers() -> None:
    assert normalize_execution_tier("prod") is ExecutionTier.FULL
    assert is_framework_only_tier(ExecutionTier.STANDARD)
    assert allows_certification(ExecutionTier.SMOKE)
    assert requires_real_inference("full")
    assert not requires_real_inference("standard")


def test_behavioral_oracle_defers_without_corpus() -> None:
    oracle = BehavioralOracle(
        metadata=behavioral_oracle_metadata(
            oracle_id="coding.oracle.behavior.python",
            name="Python Behavior",
            description="test",
            supported_profile="coding",
        ),
        behavior_runner=BehaviorRunner.create_default(),
    )
    from aiodoo_validation.domain.oracle import OracleContext

    result = oracle.execute(
        OracleContext(
            run_id="r1",
            profile_name="coding",
            plan_digest="digest",
            protocol_major=1,
            protocol_minor=0,
            execution_tier=ExecutionTier.SMOKE,
        )
    )
    assert result.success is True
    assert result.metadata["deferred"] is True
    assert result.metadata["validation_kind"] == ValidationKind.BEHAVIORAL.value


def test_build_deferred_behavioral_oracles_for_profiles() -> None:
    oracles = build_deferred_behavioral_oracles(profile="planner")
    assert oracles
    assert all(
        item.metadata.capabilities.validation_kind is ValidationKind.BEHAVIORAL for item in oracles
    )
    assert any("planner.oracle.behavior" in item.metadata.oracle_id for item in oracles)
