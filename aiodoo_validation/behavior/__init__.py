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
from aiodoo_validation.contract.parser_bridge import ContractParseError, parse_capability_output
from aiodoo_validation.domain.behavior import (
    BehaviorCase,
    BehaviorCorpus,
    BehaviorResult,
    BehaviorSuiteResult,
    ExpectedOutput,
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
        contract_mapped = bool(case.metadata.get("contract_mapped"))
        contract_prompt_text = case.metadata.get("contract_prompt_text")
        prompt_text = (
            contract_prompt_text
            if contract_mapped and isinstance(contract_prompt_text, str) and contract_prompt_text
            else case.prompt.text
        )
        outcome = inference_runner.generate(
            context,
            GenerationRequest(prompt=prompt_text),
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
                metadata=MappingProxyType(
                    {"inference_success": False, "contract_mapped": contract_mapped}
                ),
            )

        inference = outcome.result

        if contract_mapped:
            capability_id = case.metadata.get("contract_capability")
            try:
                parsed_output = parse_capability_output(
                    str(capability_id), inference.generated_text
                )
            except ContractParseError as exc:
                duration_ms = max(0, int((perf_counter() - started) * 1000))
                generated = GeneratedOutput(
                    text=inference.generated_text,
                    prompt_tokens=inference.prompt_tokens,
                    completion_tokens=inference.completion_tokens,
                    total_tokens=inference.total_tokens,
                    latency_ms=inference.latency_ms,
                    memory_usage_mb=inference.memory_usage_mb,
                    runtime=inference.metadata.runtime,
                )
                return BehaviorResult(
                    case_id=case.case_id,
                    passed=False,
                    message=f"Contract-mapped generation did not decode: {exc}",
                    comparator_kind=case.comparator_kind,
                    generated=generated,
                    expected=case.expected,
                    findings=("contract_parse_failed",),
                    duration_ms=duration_ms,
                    metadata=MappingProxyType(
                        {
                            "inference_success": True,
                            "contract_mapped": True,
                            "contract_response_valid": False,
                            "contract_error": str(exc),
                        }
                    ),
                )
            comparable_text = parsed_output.comparable_text
        else:
            comparable_text = inference.generated_text

        generated = GeneratedOutput(
            text=comparable_text,
            prompt_tokens=inference.prompt_tokens,
            completion_tokens=inference.completion_tokens,
            total_tokens=inference.total_tokens,
            latency_ms=inference.latency_ms,
            memory_usage_mb=inference.memory_usage_mb,
            runtime=inference.metadata.runtime,
        )
        comparator = self.comparator_registry.get(case.comparator_kind)
        # `aiodoo_contract`'s schemas set ``str_strip_whitespace=True`` on
        # every string field (ADR-0007's ``ContractModel``): any text that
        # round-trips through a contract response — ``comparable_text``
        # above — has its surrounding whitespace normalized away by
        # construction, regardless of what the model actually emitted.
        # Comparing that against an un-normalized ``case.expected.text``
        # would make an EXACT comparator spuriously fail on
        # leading/trailing whitespace alone for every contract-mapped
        # capability. Strip the expected side identically before
        # comparison so both sides go through the same normalization —
        # `BehaviorResult.expected` below still reports the original,
        # un-normalized gold text for traceability.
        comparison_expected = (
            ExpectedOutput(text=case.expected.text.strip(), metadata=case.expected.metadata)
            if contract_mapped
            else case.expected
        )
        comparison = comparator.compare(expected=comparison_expected, generated=generated)
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
                    "contract_mapped": contract_mapped,
                    **({"contract_response_valid": True} if contract_mapped else {}),
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
