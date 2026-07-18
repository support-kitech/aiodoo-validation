"""Planner Capability Pack exceptions."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class PlannerParseError(AiodooValidationError):
    """Raised when Planner JSON cannot be converted to ParsedCapabilityRecord."""


__all__ = ["PlannerParseError"]
