"""Inference artifact compatibility checks (Phase 3)."""

from __future__ import annotations

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import ArtifactType, InferenceErrorCode
from aiodoo_validation.domain.inference import InferenceError

SUPPORTED_MODEL_FAMILIES = frozenset({"qwen"})
SUPPORTED_MODEL_IDENTIFIERS = frozenset(
    {
        "qwen3-8b",
        "qwen/qwen3-8b",
    }
)
REJECTED_ADAPTER_TYPES = frozenset({"planner", "repair", "conversation", "execution", "evaluation"})


def _normalize(value: object) -> str:
    return str(value).strip().lower()


def validate_inference_artifacts(bundle: ArtifactBundle) -> tuple[InferenceError, ...]:
    """Validate bundle artifacts for Qwen3-8B + coding adapter inference."""
    errors: list[InferenceError] = []

    if bundle.base_model.artifact_type is not ArtifactType.BASE_MODEL:
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_MODEL,
                message="Base model artifact is required for inference.",
                field="base_model",
            )
        )

    if bundle.adapter.artifact_type is not ArtifactType.CODING_ADAPTER:
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_ADAPTER,
                message="Coding adapter artifact is required for inference.",
                field="adapter",
            )
        )

    base_meta = bundle.base_model.metadata
    model_family = _normalize(base_meta.get("model_family", ""))
    model_identifier = _normalize(
        base_meta.get("identifier", base_meta.get("model_id", ""))
    )
    if model_family and model_family not in SUPPORTED_MODEL_FAMILIES:
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_MODEL,
                message=f"Unsupported model family {model_family!r}.",
                field="base_model",
            )
        )
    if model_identifier and model_identifier not in SUPPORTED_MODEL_IDENTIFIERS:
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_MODEL,
                message=f"Unsupported model identifier {model_identifier!r}.",
                field="base_model",
            )
        )

    adapter_type = _normalize(bundle.adapter.metadata.get("adapter_type", ""))
    if adapter_type in REJECTED_ADAPTER_TYPES:
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_ADAPTER,
                message=f"Adapter type {adapter_type!r} is not supported.",
                field="adapter",
            )
        )
    elif adapter_type != "coding":
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_ADAPTER,
                message="Only coding adapters are supported in Phase 3.",
                field="adapter",
            )
        )

    return tuple(errors)
