"""Generic capability pack contract for production wiring (E5)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from aiodoo_validation.domain.capability_record import ParsedCapabilityRecord
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


class CapabilityRecordParser(Protocol):
    """Capability-agnostic parser contract used by production wiring."""

    def parse(self, data: Mapping[str, Any]) -> ParsedCapabilityRecord: ...

    def parse_training_example(
        self,
        data: Mapping[str, Any],
    ) -> tuple[ParsedCapabilityRecord, ...]: ...


@dataclass(frozen=True, slots=True)
class RegisteredCapabilityPack:
    """Generic registered capability pack (no pack-specific types)."""

    specification: CapabilitySpecification
    parser: CapabilityRecordParser
    parser_id: str

    @property
    def capability_id(self) -> str:
        return self.specification.id


__all__ = [
    "CapabilityRecordParser",
    "RegisteredCapabilityPack",
]
