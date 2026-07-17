"""Real inference runner (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import InferenceErrorCode, InferenceLifecycleState
from aiodoo_validation.domain.inference import (
    GenerationRequest,
    InferenceError,
    InferenceGenerationOutcome,
    InferenceInitializationOutcome,
    InferenceSession,
)
from aiodoo_validation.inference.compatibility import validate_runtime_artifacts
from aiodoo_validation.inference.paths import extract_load_paths
from aiodoo_validation.inference.runtime.port import LoadedModelHandle, ModelRuntimePort


@dataclass
class _ActiveInference:
    handle: LoadedModelHandle
    session: InferenceSession


@dataclass
class RealInferenceRunner:
    """Load validated artifacts and execute generation through a model runtime."""

    runtime: ModelRuntimePort
    _active: dict[str, _ActiveInference] = field(default_factory=dict)

    def initialize(self, context: RunContext) -> InferenceInitializationOutcome:
        try:
            return self._initialize(context)
        except InferenceError as exc:
            return InferenceInitializationOutcome(
                success=False,
                message="Inference initialization failed.",
                errors=(exc,),
            )
        except OSError as exc:
            return InferenceInitializationOutcome(
                success=False,
                message="Inference initialization failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.RUNNER_FAILURE,
                        message=str(exc),
                    ),
                ),
            )
        except Exception as exc:  # noqa: BLE001 — runner must never crash callers
            return InferenceInitializationOutcome(
                success=False,
                message="Inference initialization failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.RUNNER_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _initialize(self, context: RunContext) -> InferenceInitializationOutcome:
        bundle = context.artifact_bundle
        if bundle is None:
            return InferenceInitializationOutcome(
                success=False,
                message="Inference initialization failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.MISSING_BUNDLE,
                        message="Artifact bundle is required before inference.",
                        field="artifact_bundle",
                    ),
                ),
            )

        compatibility_errors = validate_runtime_artifacts(bundle)
        if compatibility_errors:
            return InferenceInitializationOutcome(
                success=False,
                message="Inference initialization failed.",
                errors=compatibility_errors,
            )

        paths, path_error = extract_load_paths(bundle)
        if path_error is not None or paths is None:
            return InferenceInitializationOutcome(
                success=False,
                message="Inference initialization failed.",
                errors=(path_error or InferenceError(
                    code=InferenceErrorCode.MISSING_BUNDLE,
                    message="Missing artifact load paths.",
                ),),
            )

        model_identifier = str(bundle.base_model.metadata.get("identifier", "qwen3-8b"))
        adapter_type = str(bundle.adapter.metadata.get("adapter_type", "coding"))

        try:
            handle = self.runtime.load(bundle, paths)
            self.runtime.verify(handle)
        except InferenceError as exc:
            return InferenceInitializationOutcome(
                success=False,
                message="Inference initialization failed.",
                errors=(exc,),
            )

        session = InferenceSession(
            run_id=context.run_id,
            bundle_digest=bundle.bundle_digest,
            lifecycle_state=InferenceLifecycleState.READY,
            model_identifier=model_identifier,
            adapter_type=adapter_type,
            runtime=self.runtime.runtime_name,
            ready=True,
        )
        self._active[context.run_id] = _ActiveInference(handle=handle, session=session)
        return InferenceInitializationOutcome(
            success=True,
            message="Inference runtime ready.",
            session=session,
        )

    def generate(
        self,
        context: RunContext,
        request: GenerationRequest,
    ) -> InferenceGenerationOutcome:
        try:
            return self._generate(context, request)
        except InferenceError as exc:
            return InferenceGenerationOutcome(
                success=False,
                message="Generation failed.",
                errors=(exc,),
            )
        except Exception as exc:  # noqa: BLE001
            return InferenceGenerationOutcome(
                success=False,
                message="Generation failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.GENERATION_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _generate(
        self,
        context: RunContext,
        request: GenerationRequest,
    ) -> InferenceGenerationOutcome:
        if not request.prompt.strip():
            return InferenceGenerationOutcome(
                success=False,
                message="Generation failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.UNSUPPORTED_CONFIG,
                        message="Prompt must be non-empty.",
                        field="prompt",
                    ),
                ),
            )
        if request.max_tokens <= 0:
            return InferenceGenerationOutcome(
                success=False,
                message="Generation failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.UNSUPPORTED_CONFIG,
                        message="max_tokens must be > 0.",
                        field="max_tokens",
                    ),
                ),
            )

        active = self._active.get(context.run_id)
        if active is None:
            return InferenceGenerationOutcome(
                success=False,
                message="Generation failed.",
                errors=(
                    InferenceError(
                        code=InferenceErrorCode.NOT_INITIALIZED,
                        message="Inference session is not initialized.",
                    ),
                ),
            )

        result = self.runtime.generate(active.handle, request)
        return InferenceGenerationOutcome(
            success=True,
            message="Generation completed.",
            result=result,
        )

    def shutdown(self, context: RunContext) -> None:
        active = self._active.pop(context.run_id, None)
        if active is None:
            return
        try:
            self.runtime.unload(active.handle)
        except Exception:  # noqa: BLE001 — cleanup must not raise
            return
