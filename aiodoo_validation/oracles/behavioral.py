"""Behavioral oracle architecture — plugs into the existing Oracle protocol.

Behavioral oracles are **not** enabled in production plans until an evaluation
corpus is supplied. Structural oracles remain the active production path.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.behavior import BehaviorRunner
from aiodoo_validation.domain.behavior import (
    BehaviorCorpus,
    BehaviorResult,
    empty_behavior_corpus,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ValidationKind
from aiodoo_validation.domain.oracle import (
    OracleCapability,
    OracleContext,
    OracleMetadata,
    OracleResult,
)
from aiodoo_validation.ports.inference_runner import InferenceRunnerPort

CorpusProvider = Callable[[OracleContext], BehaviorCorpus]
InferenceProvider = Callable[[OracleContext], InferenceRunnerPort | None]


def _default_corpus(context: OracleContext) -> BehaviorCorpus:
    return empty_behavior_corpus(profile_name=context.profile_name)


def _default_inference(_context: OracleContext) -> InferenceRunnerPort | None:
    # Wired by callers that have a live InferenceRunnerPort; default is deferred.
    return None


@dataclass(frozen=True, slots=True)
class BehavioralOracle:
    """
    Oracle that runs prompt → inference → comparator when a corpus exists.

    Without a corpus or inference runner, returns a deferred soft result that
    does not invent pass/fail certification data (``deferred=True``).
    """

    metadata: OracleMetadata
    behavior_runner: BehaviorRunner
    corpus_provider: CorpusProvider = _default_corpus
    inference_provider: InferenceProvider = _default_inference

    def execute(self, context: OracleContext) -> OracleResult:
        started = perf_counter()
        corpus = self.corpus_provider(context)
        runner = self.inference_provider(context)
        if corpus.is_empty or runner is None:
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            reason = (
                "No behavioral corpus attached."
                if corpus.is_empty
                else "No inference runner available for behavioral evaluation."
            )
            return OracleResult(
                oracle_id=self.metadata.oracle_id,
                success=True,
                message=f"Behavioral evaluation deferred: {reason}",
                findings=("behavioral_deferred",),
                warnings=(reason,),
                duration_ms=duration_ms,
                metadata=MappingProxyType(
                    {
                        "placeholder": False,
                        "deferred": True,
                        "validation_kind": ValidationKind.BEHAVIORAL.value,
                        "corpus_id": corpus.corpus_id,
                        "case_count": 0,
                    }
                ),
            )

        # BehaviorRunner expects RunContext; build a minimal shim from OracleContext.
        run_context = _run_context_from_oracle(context)
        suite = self.behavior_runner.run_suite(
            context=run_context,
            corpus=corpus,
            inference_runner=runner,
            suite_id=self.metadata.oracle_id,
        )
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        if suite.deferred:
            return OracleResult(
                oracle_id=self.metadata.oracle_id,
                success=True,
                message=suite.deferred_reason or "Behavioral evaluation deferred.",
                findings=("behavioral_deferred",),
                warnings=(suite.deferred_reason,) if suite.deferred_reason else (),
                duration_ms=duration_ms,
                metadata=MappingProxyType(
                    {
                        "placeholder": False,
                        "deferred": True,
                        "validation_kind": ValidationKind.BEHAVIORAL.value,
                        "suite": suite.suite_id,
                    }
                ),
            )

        passed = suite.all_passed
        return OracleResult(
            oracle_id=self.metadata.oracle_id,
            success=passed,
            message=(
                f"Behavioral suite {suite.suite_id}: {suite.pass_count}/{suite.case_count} passed."
            ),
            findings=tuple(
                f"{item.case_id}:{'pass' if item.passed else 'fail'}" for item in suite.results
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "deferred": False,
                    "validation_kind": ValidationKind.BEHAVIORAL.value,
                    "case_count": suite.case_count,
                    "pass_count": suite.pass_count,
                    "fail_count": suite.fail_count,
                    "pass_rate": (
                        (100.0 * suite.pass_count / suite.case_count) if suite.case_count else None
                    ),
                    "tokens_per_sec": _tokens_per_sec(suite.results),
                    "memory_mb": _max_memory(suite.results),
                    "latency_ms": suite.duration_ms,
                }
            ),
        )


def behavioral_oracle_metadata(
    *,
    oracle_id: str,
    name: str,
    description: str,
    supported_profile: str,
) -> OracleMetadata:
    return OracleMetadata(
        oracle_id=oracle_id,
        name=name,
        description=description,
        version="0.1.0-architecture",
        supported_profile=supported_profile,
        capabilities=OracleCapability(
            placeholder=False,
            reads_artifacts=False,
            uses_inference=True,
            validation_kind=ValidationKind.BEHAVIORAL,
        ),
    )


def default_behavioral_oracle_specs(profile: str) -> tuple[tuple[str, str, str], ...]:
    """ID/name/description triples for future behavioral oracles (not registered)."""
    names = (
        ("python", "Python Behavior Oracle", "Behavioral Python generation checks."),
        ("xml", "XML Behavior Oracle", "Behavioral Odoo XML generation checks."),
        ("security", "Security Behavior Oracle", "Behavioral security checks."),
        ("module_structure", "Module Structure Behavior Oracle", "Behavioral module checks."),
        ("conversation", "Conversation Behavior Oracle", "Conversation turn checks."),
        ("planner", "Planner Behavior Oracle", "Planner plan quality checks."),
        ("repair", "Repair Behavior Oracle", "Repair edit quality checks."),
        ("execution", "Execution Behavior Oracle", "Execution plan checks."),
        ("approval", "Approval Behavior Oracle", "Approval decision checks."),
        ("evaluation", "Evaluation Behavior Oracle", "Evaluation rubric checks."),
    )
    return tuple((f"{profile}.oracle.behavior.{key}", title, desc) for key, title, desc in names)


def build_deferred_behavioral_oracles(
    *,
    profile: str,
) -> tuple[BehavioralOracle, ...]:
    """
    Construct behavioral oracle instances for architecture/tests.

    Not registered in ProductionPipelineComponents until corpora exist.
    """
    runner = BehaviorRunner.create_default()
    return tuple(
        BehavioralOracle(
            metadata=behavioral_oracle_metadata(
                oracle_id=oracle_id,
                name=name,
                description=description,
                supported_profile=profile,
            ),
            behavior_runner=runner,
        )
        for oracle_id, name, description in default_behavioral_oracle_specs(profile)
    )


def _run_context_from_oracle(context: OracleContext) -> RunContext:
    from aiodoo_validation.domain.request import ValidationRequest

    request = ValidationRequest(
        profile_name=context.profile_name,
        base_model_ref="behavioral://base",
        adapter_ref="behavioral://adapter",
        execution_tier=context.execution_tier,
        protocol_major=context.protocol_major,
        protocol_minor=context.protocol_minor,
        run_id=context.run_id,
    )
    run = RunContext.begin(request)
    if context.artifact_bundle is not None:
        run = run.with_artifact_bundle(context.artifact_bundle)
    if context.inference_session is not None:
        run = run.with_inference_session(context.inference_session)
    return run


def _tokens_per_sec(results: tuple[BehaviorResult, ...]) -> float | None:
    total_tokens = 0
    total_ms = 0
    for item in results:
        generated = item.generated
        if generated is None:
            continue
        if generated.total_tokens is None or generated.latency_ms is None:
            continue
        if generated.latency_ms <= 0:
            continue
        total_tokens += int(generated.total_tokens)
        total_ms += int(generated.latency_ms)
    if total_ms <= 0 or total_tokens <= 0:
        return None
    return (total_tokens / total_ms) * 1000.0


def _max_memory(results: tuple[BehaviorResult, ...]) -> float | None:
    values = [
        item.generated.memory_usage_mb
        for item in results
        if item.generated is not None and item.generated.memory_usage_mb is not None
    ]
    return max(values) if values else None


__all__ = [
    "BehavioralOracle",
    "build_deferred_behavioral_oracles",
    "behavioral_oracle_metadata",
    "default_behavioral_oracle_specs",
]
