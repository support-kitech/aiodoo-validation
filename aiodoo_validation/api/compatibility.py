"""Compatibility helpers for ecosystem consumers (Phase 11)."""

from __future__ import annotations

from aiodoo_validation.domain.enums import ExecutionTier
from aiodoo_validation.domain.request import (
    SUPPORTED_ODOO_VERSIONS,
    SUPPORTED_PROFILES,
    SUPPORTED_PROTOCOL_MAJOR,
)


def is_protocol_supported(protocol_major: int, protocol_minor: int = 0) -> bool:
    """Return whether the Validation Protocol version is supported."""
    if protocol_major != SUPPORTED_PROTOCOL_MAJOR:
        return False
    return protocol_minor >= 0


def is_profile_supported(profile_name: str) -> bool:
    """Return whether a validation profile name is supported."""
    return profile_name in SUPPORTED_PROFILES


def is_odoo_version_supported(version: int) -> bool:
    """Return whether an Odoo major version is supported."""
    return version in SUPPORTED_ODOO_VERSIONS


def is_execution_tier_supported(tier: str) -> bool:
    """Return whether an execution tier name is supported."""
    try:
        ExecutionTier(tier)
    except ValueError:
        return False
    return True
