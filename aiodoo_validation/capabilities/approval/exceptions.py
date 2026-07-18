"""Approval Capability Pack exceptions."""

from __future__ import annotations

from aiodoo_validation.exceptions import AiodooValidationError


class ApprovalParseError(AiodooValidationError):
    """Raised when Approval JSON cannot be converted to ParsedCapabilityRecord."""


__all__ = ["ApprovalParseError"]
