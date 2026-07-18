"""Repair Capability Pack exceptions."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class RepairParseError(AiodooValidationError):
    """Raised when Repair JSON cannot be converted to ParsedCapabilityRecord."""


__all__ = ["RepairParseError"]
