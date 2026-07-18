"""Behavior case builder exceptions (Capability Delivery E3)."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class BehaviorCaseBuildError(AiodooValidationError):
    """Raised when a ParsedCapabilityRecord cannot be assembled into cases."""


__all__ = ["BehaviorCaseBuildError"]
