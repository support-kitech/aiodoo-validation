"""Normalized capability record domain types (parser output).

Generic only — no Repair/Linux/schema-specific fields. Packs map native
schemas into these types; opaque transform payloads stay in ``payload``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.freeze import freeze_mapping
from aiodoo_validation.exceptions import DomainError


@dataclass(frozen=True, slots=True)
class CapabilityArtifact:
    """One artifact span or file fragment referenced by a capability record."""

    artifact_id: str
    path: str
    content: str = ""
    media_type: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise DomainError("artifact_id must be non-empty.")
        if not self.path.strip():
            raise DomainError("path must be non-empty.")
        if self.media_type is not None and not self.media_type.strip():
            raise DomainError("media_type must be non-empty when provided.")
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class TransformationDescriptor:
    """
    Opaque declarative transformation.

    ``transformation_type`` is a string id (e.g. ``replace``). ``payload`` is
    pack-defined and interpreted by TransformationEngine / pack adapters later.
    """

    transformation_type: str
    payload: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.transformation_type.strip():
            raise DomainError("transformation_type must be non-empty.")
        object.__setattr__(self, "payload", freeze_mapping(self.payload))


@dataclass(frozen=True, slots=True)
class ParsedCapabilityRecord:
    """
    Normalized capability input after RecordParser (before BehaviorCaseBuilder).

    Intentionally free of capability-specific schema keys (no Repair ``operations``,
    no Linux shell fields). Those belong in pack parsers that fill ``payload``.
    """

    record_id: str
    capability_id: str
    problem: str
    artifacts: tuple[CapabilityArtifact, ...] = ()
    transformations: tuple[TransformationDescriptor, ...] = ()
    explanation: str | None = None
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise DomainError("record_id must be non-empty.")
        if not self.capability_id.strip():
            raise DomainError("capability_id must be non-empty.")
        # problem may be empty for artifact-only records; keep as str always.
        if not isinstance(self.problem, str):
            raise DomainError("problem must be a string.")
        if self.explanation is not None and not isinstance(self.explanation, str):
            raise DomainError("explanation must be a string when provided.")

        artifacts = tuple(self.artifacts)
        if not all(isinstance(item, CapabilityArtifact) for item in artifacts):
            raise DomainError("artifacts must contain CapabilityArtifact values only.")
        artifact_ids = [item.artifact_id for item in artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise DomainError("artifacts must not contain duplicate artifact_id values.")

        transforms = tuple(self.transformations)
        if not all(isinstance(item, TransformationDescriptor) for item in transforms):
            raise DomainError(
                "transformations must contain TransformationDescriptor values only."
            )

        tags = tuple(str(tag) for tag in self.tags)
        if any(not tag.strip() for tag in tags):
            raise DomainError("tags entries must be non-empty strings.")
        if len(tags) != len(set(tags)):
            raise DomainError("tags must not contain duplicates.")

        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(self, "transformations", transforms)
        object.__setattr__(self, "tags", tags)
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


__all__ = [
    "CapabilityArtifact",
    "ParsedCapabilityRecord",
    "TransformationDescriptor",
]
