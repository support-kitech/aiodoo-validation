"""Artifact compatibility validation (Phase 2)."""

from __future__ import annotations

from aiodoo_validation.domain.artifacts import ArtifactDescriptor
from aiodoo_validation.domain.enums import (
    ArtifactResolutionErrorCode,
    ArtifactType,
    SupportedValidationProfile,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.resolution import ArtifactResolutionError

SUPPORTED_ADAPTER_TYPES = frozenset({SupportedValidationProfile.CODING.value})
REJECTED_ADAPTER_TYPES = frozenset({"planner", "repair", "conversation", "execution", "evaluation"})


def validate_profile_artifact_compatibility(
    request: ValidationRequest,
    *,
    base_model: ArtifactDescriptor,
    adapter: ArtifactDescriptor,
) -> tuple[ArtifactResolutionError, ...]:
    """Validate coding profile compatibility with resolved artifacts."""
    errors: list[ArtifactResolutionError] = []

    if base_model.artifact_type is not ArtifactType.BASE_MODEL:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.INCOMPATIBLE_ARTIFACT,
                message=f"Expected base model artifact, got {base_model.artifact_type.value}.",
                field="base_model",
            )
        )

    if adapter.artifact_type is not ArtifactType.CODING_ADAPTER:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.INCOMPATIBLE_ARTIFACT,
                message=f"Expected coding adapter artifact, got {adapter.artifact_type.value}.",
                field="adapter",
            )
        )

    adapter_type = str(adapter.metadata.get("adapter_type", "")).strip().lower()
    if adapter_type in REJECTED_ADAPTER_TYPES:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.UNSUPPORTED_ARTIFACT,
                message=f"Adapter type {adapter_type!r} is not supported in Phase 2.",
                field="adapter",
            )
        )
    elif adapter_type and adapter_type not in SUPPORTED_ADAPTER_TYPES:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.UNSUPPORTED_ARTIFACT,
                message=f"Unsupported adapter_type {adapter_type!r}.",
                field="adapter",
            )
        )
    elif (
        request.profile_name == SupportedValidationProfile.CODING.value
        and adapter_type != "coding"
    ):
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.INCOMPATIBLE_ARTIFACT,
                message="Coding profile requires adapter_type='coding'.",
                field="adapter",
            )
        )

    return tuple(errors)


def validate_no_duplicate_locations(
    descriptors: tuple[ArtifactDescriptor, ...],
) -> tuple[ArtifactResolutionError, ...]:
    """Reject when multiple artifacts resolve to the same location digest."""
    seen: dict[str, str] = {}
    errors: list[ArtifactResolutionError] = []
    for descriptor in descriptors:
        prior = seen.get(descriptor.location_digest)
        if prior is not None:
            errors.append(
                ArtifactResolutionError(
                    code=ArtifactResolutionErrorCode.DUPLICATE_ARTIFACT,
                    message=(
                        f"Duplicate artifact location for {descriptor.logical_ref!r} "
                        f"and {prior!r}."
                    ),
                    field=descriptor.logical_ref,
                )
            )
            continue
        seen[descriptor.location_digest] = descriptor.logical_ref
    return tuple(errors)
