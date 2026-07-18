"""Evaluation Capability Pack exceptions."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class EvaluationParseError(AiodooValidationError):
    """Raised when Evaluation JSON cannot be converted to ParsedCapabilityRecord."""


__all__ = ["EvaluationParseError"]
