"""Inference runtime compatibility checks (Phase 3)."""

from __future__ import annotations

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import ArtifactType, InferenceErrorCode
from aiodoo_validation.domain.inference import InferenceError
from aiodoo_validation.inference.runtime_policy import (
    SUPPORTED_RUNTIME_MODEL_FAMILIES,
    SUPPORTED_RUNTIME_MODEL_IDENTIFIERS,
)


def _normalize(value: object) -> str:
    return str(value).strip().lower()


def validate_runtime_artifacts(bundle: ArtifactBundle) -> tuple[InferenceError, ...]:
    """Validate bundle artifacts for inference runtime loading."""
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
                message="Adapter artifact is required for inference.",
                field="adapter",
            )
        )

    base_meta = bundle.base_model.metadata
    model_family = _normalize(base_meta.get("model_family", ""))
    model_identifier = _normalize(base_meta.get("identifier", base_meta.get("model_id", "")))
    if model_family and model_family not in SUPPORTED_RUNTIME_MODEL_FAMILIES:
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_MODEL,
                message=f"Unsupported runtime model family {model_family!r}.",
                field="base_model",
            )
        )
    if model_identifier and model_identifier not in SUPPORTED_RUNTIME_MODEL_IDENTIFIERS:
        errors.append(
            InferenceError(
                code=InferenceErrorCode.UNSUPPORTED_MODEL,
                message=f"Unsupported runtime model identifier {model_identifier!r}.",
                field="base_model",
            )
        )

    return tuple(errors)
