"""Transformation package exceptions (Capability Delivery E2)."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class TransformationError(AiodooValidationError):
    """Base error for transformation package failures."""


class TransformationValidationError(TransformationError):
    """Raised when a transformation or snapshot violates invariants."""


__all__ = [
    "TransformationError",
    "TransformationValidationError",
]
