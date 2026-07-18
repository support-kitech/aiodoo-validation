"""Production capability behavioral oracle (E5 integration)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.behavior import BehaviorRunner
from aiodoo_validation.behavior.capability_pipeline import (
    CapabilityBehaviorPipeline,
    CapabilityPipelineError,
)
from aiodoo_validation.capabilities.registry import (
    CapabilityRegistry,
    CapabilityRegistryError,
)
from aiodoo_validation.corpus.exceptions import CorpusError, CorpusGateError, CorpusLoadError
from aiodoo_validation.corpus.provider import (
    EVALUATION_CORPUS_PATH_KEY,
    ConfigurableCorpusProvider,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ValidationKind
from aiodoo_validation.domain.oracle import (
    OracleCapability,
    OracleContext,
    OracleMetadata,
    OracleResult,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.ports.inference_runner import InferenceRunnerPort

InferenceProvider = Callable[[OracleContext], InferenceRunnerPort | None]


def _run_context_from_oracle(context: OracleContext) -> RunContext:
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


@dataclass(frozen=True, slots=True)
class CapabilityBehavioralOracle:
    """
    Production behavioral oracle for a registered capability.

    Missing corpus path → deferred (structural cert unchanged).
    Invalid corpus path / gate / parse failures → hard error result.
    """

    metadata: OracleMetadata
    capability_id: str
    capability_registry: CapabilityRegistry
    corpus_provider: ConfigurableCorpusProvider
    pipeline: CapabilityBehaviorPipeline
    behavior_runner: BehaviorRunner
    inference_provider: InferenceProvider

    def execute(self, context: OracleContext) -> OracleResult:
        started = perf_counter()
        configured = context.configuration.get(EVALUATION_CORPUS_PATH_KEY)
        try:
            loaded = self.corpus_provider.load(configured)
        except (CorpusLoadError, CorpusGateError, CorpusError) as exc:
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            return OracleResult(
                oracle_id=self.metadata.oracle_id,
                success=False,
                message=f"Evaluation corpus error: {exc}",
                findings=("corpus_error",),
                errors=(),
                duration_ms=duration_ms,
                metadata=MappingProxyType(
                    {
                        "deferred": False,
                        "validation_kind": ValidationKind.BEHAVIORAL.value,
                        "capability_id": self.capability_id,
                        "error_type": type(exc).__name__,
                    }
                ),
            )

        if loaded is None:
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            reason = (
                f"No {EVALUATION_CORPUS_PATH_KEY!r} configured for "
                f"capability {self.capability_id!r}."
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
                        "deferred": True,
                        "validation_kind": ValidationKind.BEHAVIORAL.value,
                        "capability_id": self.capability_id,
                        "case_count": 0,
                    }
                ),
            )

        try:
            pack = self.capability_registry.get(self.capability_id)
            assembled = self.pipeline.assemble(loaded, pack)
        except (CapabilityRegistryError, CapabilityPipelineError) as exc:
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            return OracleResult(
                oracle_id=self.metadata.oracle_id,
                success=False,
                message=str(exc),
                findings=("capability_pipeline_error",),
                duration_ms=duration_ms,
                metadata=MappingProxyType(
                    {
                        "deferred": False,
                        "validation_kind": ValidationKind.BEHAVIORAL.value,
                        "capability_id": self.capability_id,
                        "error_type": type(exc).__name__,
                    }
                ),
            )

        runner = self.inference_provider(context)
        if runner is None:
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            reason = "No inference runner available for behavioral evaluation."
            return OracleResult(
                oracle_id=self.metadata.oracle_id,
                success=True,
                message=f"Behavioral evaluation deferred: {reason}",
                findings=("behavioral_deferred",),
                warnings=(reason,),
                duration_ms=duration_ms,
                metadata=MappingProxyType(
                    {
                        "deferred": True,
                        "validation_kind": ValidationKind.BEHAVIORAL.value,
                        "capability_id": self.capability_id,
                        "corpus_id": assembled.corpus.corpus_id,
                        "fingerprint": loaded.manifest.fingerprint,
                        "transforms_passed": assembled.transforms_passed,
                    }
                ),
            )

        run_context = _run_context_from_oracle(context)
        suite = self.behavior_runner.run_suite(
            context=run_context,
            corpus=assembled.corpus,
            inference_runner=runner,
            suite_id=self.metadata.oracle_id,
        )
        duration_ms = max(0, int((perf_counter() - started) * 1000))

        transform_ok = assembled.transforms_passed
        behavior_ok = (not suite.deferred) and suite.all_passed
        success = transform_ok and behavior_ok and not suite.deferred

        findings = [
            f"transform:{'pass' if transform_ok else 'fail'}",
            *(f"{item.case_id}:{'pass' if item.passed else 'fail'}" for item in suite.results),
        ]
        if suite.deferred:
            findings.insert(0, "behavioral_deferred")

        provenance = {
            "deferred": bool(suite.deferred),
            "validation_kind": ValidationKind.BEHAVIORAL.value,
            "capability_id": self.capability_id,
            "corpus_id": assembled.corpus.corpus_id,
            "fingerprint": loaded.manifest.fingerprint,
            "computed_fingerprint": loaded.computed_fingerprint,
            "dataset_version": loaded.manifest.dataset_version,
            "source_package": loaded.manifest.source_package,
            "case_count": suite.case_count,
            "pass_count": suite.pass_count,
            "fail_count": suite.fail_count,
            "transforms_passed": transform_ok,
            "transform_case_count": len(assembled.transform_results),
        }
        message = (
            f"Capability behavior {self.capability_id}: "
            f"transforms={'pass' if transform_ok else 'fail'}, "
            f"suite={suite.pass_count}/{suite.case_count} passed."
        )
        if suite.deferred:
            message = suite.deferred_reason or message

        return OracleResult(
            oracle_id=self.metadata.oracle_id,
            success=success if not suite.deferred else True,
            message=message,
            findings=tuple(findings),
            warnings=((suite.deferred_reason,) if suite.deferred and suite.deferred_reason else ()),
            duration_ms=duration_ms,
            metadata=MappingProxyType(provenance),
        )


def repair_behavior_oracle_id() -> str:
    return "repair.oracle.behavior.repair"


def coding_behavior_oracle_id() -> str:
    return "coding.oracle.behavior.coding"


def planner_behavior_oracle_id() -> str:
    return "planner.oracle.behavior.planner"


def conversation_behavior_oracle_id() -> str:
    return "conversation.oracle.behavior.conversation"


def build_capability_behavioral_oracle(
    *,
    capability_id: str,
    oracle_id: str,
    name: str,
    description: str,
    capability_registry: CapabilityRegistry,
    inference_runner: InferenceRunnerPort,
    corpus_provider: ConfigurableCorpusProvider | None = None,
    pipeline: CapabilityBehaviorPipeline | None = None,
    behavior_runner: BehaviorRunner | None = None,
) -> CapabilityBehavioralOracle:
    def inference_provider(context: OracleContext) -> InferenceRunnerPort | None:
        if context.inference_session is None:
            return None
        return inference_runner

    return CapabilityBehavioralOracle(
        metadata=OracleMetadata(
            oracle_id=oracle_id,
            name=name,
            description=description,
            version="1.0.0",
            supported_profile=capability_id,
            capabilities=OracleCapability(
                placeholder=False,
                reads_artifacts=False,
                uses_inference=True,
                validation_kind=ValidationKind.BEHAVIORAL,
            ),
        ),
        capability_id=capability_id,
        capability_registry=capability_registry,
        corpus_provider=corpus_provider or ConfigurableCorpusProvider(),
        pipeline=pipeline or CapabilityBehaviorPipeline(),
        behavior_runner=behavior_runner or BehaviorRunner.create_default(),
        inference_provider=inference_provider,
    )


__all__ = [
    "CapabilityBehavioralOracle",
    "build_capability_behavioral_oracle",
    "coding_behavior_oracle_id",
    "conversation_behavior_oracle_id",
    "planner_behavior_oracle_id",
    "repair_behavior_oracle_id",
]
