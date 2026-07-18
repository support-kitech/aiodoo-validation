"""Execution Capability Pack exceptions."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class ExecutionParseError(AiodooValidationError):
    """Raised when Execution JSON cannot be converted to ParsedCapabilityRecord."""


__all__ = ["ExecutionParseError"]
