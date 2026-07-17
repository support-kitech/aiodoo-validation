"""Stub inference runner (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import InferenceErrorCode, InferenceLifecycleState
from aiodoo_validation.domain.inference import (
    GenerationRequest,
    InferenceError,
    InferenceGenerationOutcome,
    InferenceInitializationOutcome,
    InferenceSession,
)
from aiodoo_validation.inference.runner import RealInferenceRunner
from aiodoo_validation.inference.runtime.mock import MockModelRuntime


@dataclass(frozen=True, slots=True)
class StubInferenceRunner:
    """Mock inference runner used by default in CI."""

    _delegate: RealInferenceRunner

    @classmethod
    def create(cls) -> StubInferenceRunner:
        return cls(_delegate=RealInferenceRunner(runtime=MockModelRuntime()))

    def initialize(self, context: RunContext) -> InferenceInitializationOutcome:
        bundle = context.artifact_bundle
        if bundle is None:
            return InferenceInitializationOutcome(
                success=True,
                message="stub inference initialization",
                session=InferenceSession(
                    run_id=context.run_id,
                    bundle_digest="stub",
                    lifecycle_state=InferenceLifecycleState.READY,
                    model_identifier="qwen3-8b",
                    adapter_type="coding",
                    runtime="stub",
                    ready=True,
                ),
            )

        outcome = self._delegate.initialize(context)
        if outcome.success and outcome.session is not None:
            session = InferenceSession(
                run_id=outcome.session.run_id,
                bundle_digest=outcome.session.bundle_digest,
                lifecycle_state=outcome.session.lifecycle_state,
                model_identifier=outcome.session.model_identifier,
                adapter_type=outcome.session.adapter_type,
                runtime="stub",
                ready=True,
            )
            return InferenceInitializationOutcome(
                success=True,
                message="stub inference initialization",
                session=session,
            )
        return InferenceInitializationOutcome(
            success=True,
            message="stub inference initialization",
            session=InferenceSession(
                run_id=context.run_id,
                bundle_digest=bundle.bundle_digest,
                lifecycle_state=InferenceLifecycleState.READY,
                model_identifier=str(bundle.base_model.metadata.get("identifier", "qwen3-8b")),
                adapter_type=str(bundle.adapter.metadata.get("adapter_type", "coding")),
                runtime="stub",
                ready=True,
            ),
        )

    def generate(
        self,
        context: RunContext,
        request: GenerationRequest,
    ) -> InferenceGenerationOutcome:
        if context.artifact_bundle is None:
            return InferenceGenerationOutcome(
                success=False,
                message="Generation failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.NOT_INITIALIZED,
                        message="Stub inference requires an artifact bundle for generation.",
                    ),
                ),
            )
        return self._delegate.generate(context, request)

    def shutdown(self, context: RunContext) -> None:
        self._delegate.shutdown(context)
