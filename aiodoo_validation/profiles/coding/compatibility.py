"""Coding profile artifact compatibility (Phase 4)."""

from __future__ import annotations

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import ArtifactType, ProfileErrorCode
from aiodoo_validation.domain.profile import ProfileError
from aiodoo_validation.profiles.coding.policy import (
    REJECTED_PROFILE_NAMES,
    SUPPORTED_ADAPTER_TYPES,
    SUPPORTED_ARTIFACT_TYPES,
    SUPPORTED_MODEL_FAMILIES,
    SUPPORTED_MODEL_IDENTIFIERS,
    SUPPORTED_PROTOCOL_MAJORS,
)


def _normalize(value: object) -> str:
    return str(value).strip().lower()


def validate_coding_artifact_compatibility(bundle: ArtifactBundle) -> tuple[ProfileError, ...]:
    """Validate resolved artifacts against coding profile policy."""
    errors: list[ProfileError] = []

    if bundle.base_model.artifact_type.value not in SUPPORTED_ARTIFACT_TYPES:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_MODEL,
                message=(
                    f"Unsupported base artifact type "
                    f"{bundle.base_model.artifact_type.value!r}."
                ),
                field="base_model",
            )
        )
    elif bundle.base_model.artifact_type is not ArtifactType.BASE_MODEL:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_MODEL,
                message="Coding profile requires a base model artifact.",
                field="base_model",
            )
        )

    if bundle.adapter.artifact_type.value not in SUPPORTED_ARTIFACT_TYPES:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_ADAPTER,
                message=(
                    f"Unsupported adapter artifact type "
                    f"{bundle.adapter.artifact_type.value!r}."
                ),
                field="adapter",
            )
        )
    elif bundle.adapter.artifact_type is not ArtifactType.CODING_ADAPTER:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_ADAPTER,
                message="Coding profile requires a coding adapter artifact.",
                field="adapter",
            )
        )

    if bundle.protocol_major not in SUPPORTED_PROTOCOL_MAJORS:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_PROTOCOL,
                message=f"Unsupported protocol major {bundle.protocol_major}.",
                field="protocol_major",
            )
        )

    base_meta = bundle.base_model.metadata
    model_family = _normalize(base_meta.get("model_family", ""))
    model_identifier = _normalize(base_meta.get("identifier", base_meta.get("model_id", "")))
    if model_family and model_family not in SUPPORTED_MODEL_FAMILIES:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_MODEL,
                message=f"Unsupported model family {model_family!r}.",
                field="base_model",
            )
        )
    if model_identifier and model_identifier not in SUPPORTED_MODEL_IDENTIFIERS:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_MODEL,
                message=f"Unsupported model identifier {model_identifier!r}.",
                field="base_model",
            )
        )

    adapter_type = _normalize(bundle.adapter.metadata.get("adapter_type", ""))
    if adapter_type in REJECTED_PROFILE_NAMES:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_ADAPTER,
                message=f"Adapter type {adapter_type!r} is not supported by the coding profile.",
                field="adapter",
            )
        )
    elif adapter_type and adapter_type not in SUPPORTED_ADAPTER_TYPES:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_ADAPTER,
                message=f"Unsupported adapter_type {adapter_type!r}.",
                field="adapter",
            )
        )
    elif adapter_type != "coding":
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_ADAPTER,
                message="Coding profile requires adapter_type='coding'.",
                field="adapter",
            )
        )

    return tuple(errors)
