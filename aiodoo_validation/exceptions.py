"""Shared exception hierarchy for aiodoo-validation."""


class AiodooValidationError(Exception):
    """Base error for all aiodoo-validation failures."""


class DomainError(AiodooValidationError):
    """Raised when domain invariants are violated."""


class InvalidRequestError(AiodooValidationError):
    """Raised when a validation request fails structural validation."""


class ProtocolError(AiodooValidationError):
    """Raised when Validation Protocol version negotiation fails."""


class PipelineError(AiodooValidationError):
    """Raised when pipeline construction or stage execution fails."""
