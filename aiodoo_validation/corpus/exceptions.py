"""Corpus package exceptions (Capability Delivery E1)."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class CorpusError(AiodooValidationError):
    """Base error for corpus package failures."""


class CorpusLoadError(CorpusError):
    """Raised when a corpus cannot be loaded from disk or parsed."""


class CorpusGateError(CorpusError):
    """Raised when a corpus fails fail-closed gate evaluation."""


__all__ = [
    "CorpusError",
    "CorpusGateError",
    "CorpusLoadError",
]
