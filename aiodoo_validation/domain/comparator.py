"""Comparator domain types for behavioral validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ComparatorKind


@dataclass(frozen=True, slots=True)
class ComparatorCapability:
    """Declared capability flags for a comparator implementation."""

    implemented: bool = False
    requires_ast: bool = False
    requires_xml_parser: bool = False
    requires_json: bool = False
    requires_model: bool = False


@dataclass(frozen=True, slots=True)
class ComparatorMetadata:
    """Immutable metadata describing a registered comparator."""

    comparator_id: str
    kind: ComparatorKind
    name: str
    description: str
    version: str
    capabilities: ComparatorCapability


@dataclass(frozen=True, slots=True)
class ComparatorResult:
    """Immutable result of comparing expected vs generated output."""

    passed: bool
    similarity: float | None
    message: str
    findings: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


__all__ = [
    "ComparatorCapability",
    "ComparatorMetadata",
    "ComparatorResult",
]
