"""Validation Protocol V1 negotiation."""

from __future__ import annotations

from aiodoo_validation.domain.request import SUPPORTED_PROTOCOL_MAJOR, ValidationRequest
from aiodoo_validation.exceptions import ProtocolError


def negotiate_protocol(request: ValidationRequest) -> tuple[int, int]:
    """
    Negotiate Validation Protocol version for the request.

    Only Validation Protocol V1 (major=1) is supported.
    """
    if request.protocol_major != SUPPORTED_PROTOCOL_MAJOR:
        raise ProtocolError(
            f"Unsupported Validation Protocol major version {request.protocol_major}. "
            f"Supported major: {SUPPORTED_PROTOCOL_MAJOR}."
        )
    if request.protocol_minor < 0:
        raise ProtocolError("protocol_minor must be >= 0.")
    return request.protocol_major, request.protocol_minor
