"""Artifact structural compatibility validation (Phase 2)."""

from __future__ import annotations

from aiodoo_validation.domain.artifacts import ArtifactDescriptor
from aiodoo_validation.domain.enums import ArtifactResolutionErrorCode
from aiodoo_validation.domain.resolution import ArtifactResolutionError


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
