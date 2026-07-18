"""Comparator domain types for behavioral validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ComparatorKind


@dataclass(frozen=True, slots=True)
class ComparatorCapability:
    """
    Declared capability flags for a comparator implementation.

    Descriptive only — does not change comparator execution today.
    """

    implemented: bool = False
    # Resource / parser requirements
    requires_model: bool = False
    requires_ast: bool = False
    requires_json: bool = False
    requires_xml: bool = False
    requires_xml_parser: bool = False  # Alias retained for compatibility
    requires_python: bool = False
    requires_tokenization: bool = False
    # Execution traits
    supports_batch: bool = False
    supports_streaming: bool = False
    supports_parallel: bool = False
    supports_gpu: bool = False
    supports_cpu: bool = True
    deterministic: bool = True
    behavioral_only: bool = False
    structural_only: bool = False
    placeholder: bool = False

    def as_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(asdict(self)))


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
