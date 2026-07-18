"""Coding capability pack registration (pack-local; behavioral DI is later)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.capabilities.coding.parser import CodingRecordParser
from aiodoo_validation.capabilities.coding.specification import (
    CODING_PARSER_ID,
    build_coding_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


@dataclass(frozen=True, slots=True)
class CodingCapabilityPack:
    """
    Registered Coding capability surface for Capability Delivery.

    Pack registration is foundation (Phase 1). Behavioral oracle wiring is
    deferred to a later coding phase — same split as Repair E4 vs E5.
    """

    specification: CapabilitySpecification
    parser: CodingRecordParser
    parser_id: str = CODING_PARSER_ID

    @property
    def capability_id(self) -> str:
        return self.specification.id

    def capability_yaml(self) -> str:
        """Return declarative capability.yaml text."""
        return capability_yaml_path().read_text(encoding="utf-8")


def get_coding_capability_pack() -> CodingCapabilityPack:
    """Return the Coding pack registration (specification + parser)."""
    specification = build_coding_specification()
    if specification.parser_id != CODING_PARSER_ID:
        raise RuntimeError("Coding specification parser_id mismatch.")
    return CodingCapabilityPack(
        specification=specification,
        parser=CodingRecordParser(),
        parser_id=CODING_PARSER_ID,
    )


__all__ = [
    "CODING_PARSER_ID",
    "CodingCapabilityPack",
    "get_coding_capability_pack",
]
