"""Conversation Capability Pack exceptions."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class ConversationParseError(AiodooValidationError):
    """Raised when Conversation JSON cannot be converted to ParsedCapabilityRecord."""


__all__ = ["ConversationParseError"]
