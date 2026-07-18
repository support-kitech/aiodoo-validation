"""Coding Capability Pack exceptions."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class CodingParseError(AiodooValidationError):
    """Raised when Coding JSON cannot be converted to ParsedCapabilityRecord."""


__all__ = ["CodingParseError"]
