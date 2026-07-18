"""Shared immutable mapping helpers for domain types."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from aiodoo_validation.exceptions import DomainError


def freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return an immutable mapping copy, or an empty mapping when ``None``."""
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise DomainError("mapping field must be a mapping.")
    return MappingProxyType(dict(value))


__all__ = ["freeze_mapping"]
