"""Artifact bundle domain types (Phase 2)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ArtifactType, FingerprintPolicy


@dataclass(frozen=True, slots=True)
class ArtifactFingerprint:
    """Placeholder or future real fingerprint for an artifact."""

    value: str
    placeholder: bool = True
    algorithm: str = "placeholder-v1"


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    """
    Resolved artifact identity exposed to downstream stages.

    Raw filesystem paths are not exposed — only opaque digests and metadata.
    """

    artifact_type: ArtifactType
    logical_ref: str
    location_digest: str
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    fingerprint: ArtifactFingerprint | None = None


@dataclass(frozen=True, slots=True)
class ArtifactBundle:
    """
    Immutable bundle produced by artifact resolution.

    Downstream pipeline stages must consume this object instead of request paths.
    """

    base_model: ArtifactDescriptor
    adapter: ArtifactDescriptor
    merged_model: ArtifactDescriptor | None
    protocol_major: int
    protocol_minor: int
    fingerprint_policy: FingerprintPolicy
    bundle_digest: str
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
