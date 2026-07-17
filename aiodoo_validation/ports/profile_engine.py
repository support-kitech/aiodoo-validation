"""Profile engine port."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.profile import ProfileResolutionOutcome


class ProfileEnginePort(Protocol):
    """Resolve validation profiles and build ValidationPlan metadata (Phase 4+)."""

    def resolve_profile(self, context: RunContext) -> ProfileResolutionOutcome: ...
