"""Artifact resolver port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.resolution import ArtifactResolutionOutcome


class ArtifactResolverPort(Protocol):
    """Resolve validation artifacts into an immutable bundle (Phase 2+)."""

    def resolve(self, context: RunContext) -> ArtifactResolutionOutcome: ...
