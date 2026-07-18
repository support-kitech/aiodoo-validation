"""Behavioral evaluation — runner and Capability Delivery case builder."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.behavior.build_result import BehaviorCaseBuildResult
from aiodoo_validation.behavior.case_builder import (
    BehaviorCaseBuilder,
    descriptor_to_replace_transformation,
)
from aiodoo_validation.behavior.exceptions import BehaviorCaseBuildError
from aiodoo_validation.comparators import ComparatorRegistry
from aiodoo_validation.domain.behavior import (
    BehaviorCase,
    BehaviorCorpus,
    BehaviorResult,
    BehaviorSuiteResult,
    GeneratedOutput,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.inference import GenerationRequest
from aiodoo_validation.execution import behavior_case_limit
from aiodoo_validation.ports.inference_runner import InferenceRunnerPort


@dataclass(frozen=True, slots=True)
class BehaviorRunner:
    """
    Execute a behavioral corpus against an initialized inference runner.

    Does not invent cases. An empty corpus yields a deferred suite result.
    """

    comparator_registry: ComparatorRegistry

    @classmethod
    def create_default(cls) -> BehaviorRunner:
        return cls(comparator_registry=ComparatorRegistry.create_default())

    def run_suite(
        self,
        *,
        context: RunContext,
        corpus: BehaviorCorpus,
        inference_runner: InferenceRunnerPort,
        suite_id: str | None = None,
    ) -> BehaviorSuiteResult:
        limited = corpus.limited(behavior_case_limit(context.execution_tier))
        suite = suite_id or limited.corpus_id
        if limited.is_empty:
            return BehaviorSuiteResult(
                suite_id=suite,
                profile_name=limited.profile_name or context.request.profile_name,
                results=(),
                duration_ms=0,
                case_count=0,
                pass_count=0,
                fail_count=0,
                deferred=True,
                deferred_reason=(
                    "No behavioral evaluation corpus attached "
                    "(architecture ready; datasets not loaded)."
                ),
                metadata=MappingProxyType(
                    {
                        "execution_tier": context.execution_tier.value,
                        "corpus_id": limited.corpus_id,
                    }
                ),
            )

        started = perf_counter()
        results: list[BehaviorResult] = []
        for case in limited.cases:
            results.append(
                self.run_case(
                    context=context,
                    case=case,
                    inference_runner=inference_runner,
                )
            )
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        pass_count = sum(1 for item in results if item.passed)
        fail_count = len(results) - pass_count
        return BehaviorSuiteResult(
            suite_id=suite,
            profile_name=limited.profile_name,
            results=tuple(results),
            duration_ms=duration_ms,
            case_count=len(results),
            pass_count=pass_count,
            fail_count=fail_count,
            deferred=False,
            metadata=MappingProxyType(
                {
                    "execution_tier": context.execution_tier.value,
                    "corpus_id": limited.corpus_id,
                }
            ),
        )

    def run_case(
        self,
        *,
        context: RunContext,
        case: BehaviorCase,
        inference_runner: InferenceRunnerPort,
    ) -> BehaviorResult:
        started = perf_counter()
        outcome = inference_runner.generate(
            context,
            GenerationRequest(prompt=case.prompt.text),
        )
        if not outcome.success or outcome.result is None:
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            message = outcome.message or "Inference generation failed."
            return BehaviorResult(
                case_id=case.case_id,
                passed=False,
                message=message,
                comparator_kind=case.comparator_kind,
                expected=case.expected,
                findings=("inference_failure",),
                duration_ms=duration_ms,
                metadata=MappingProxyType({"inference_success": False}),
            )

        inference = outcome.result
        generated = GeneratedOutput(
            text=inference.generated_text,
            prompt_tokens=inference.prompt_tokens,
            completion_tokens=inference.completion_tokens,
            total_tokens=inference.total_tokens,
            latency_ms=inference.latency_ms,
            memory_usage_mb=inference.memory_usage_mb,
            runtime=inference.metadata.runtime,
        )
        comparator = self.comparator_registry.get(case.comparator_kind)
        comparison = comparator.compare(expected=case.expected, generated=generated)
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return BehaviorResult(
            case_id=case.case_id,
            passed=comparison.passed,
            message=comparison.message,
            comparator_kind=case.comparator_kind,
            similarity=comparison.similarity,
            generated=generated,
            expected=case.expected,
            findings=comparison.findings,
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "inference_success": True,
                    "comparator_id": comparator.metadata.comparator_id,
                    **dict(comparison.metadata),
                }
            ),
        )


__all__ = [
    "BehaviorCaseBuildError",
    "BehaviorCaseBuildResult",
    "BehaviorCaseBuilder",
    "BehaviorRunner",
    "descriptor_to_replace_transformation",
]
