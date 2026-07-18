"""Repair capability pack registration (pack-local; not production DI)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.capabilities.repair.parser import RepairRecordParser
from aiodoo_validation.capabilities.repair.specification import (
    REPAIR_PARSER_ID,
    build_repair_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


@dataclass(frozen=True, slots=True)
class RepairCapabilityPack:
    """
    Registered Repair capability surface for Capability Delivery.

    Not wired into ValidationEngine / production.py (that is E5).
    """

    specification: CapabilitySpecification
    parser: RepairRecordParser
    parser_id: str = REPAIR_PARSER_ID

    @property
    def capability_id(self) -> str:
        return self.specification.id

    def capability_yaml(self) -> str:
        """Return declarative capability.yaml text."""
        return capability_yaml_path().read_text(encoding="utf-8")


def get_repair_capability_pack() -> RepairCapabilityPack:
    """Return the Repair pack registration (specification + parser)."""
    specification = build_repair_specification()
    if specification.parser_id != REPAIR_PARSER_ID:
        raise RuntimeError("Repair specification parser_id mismatch.")
    return RepairCapabilityPack(
        specification=specification,
        parser=RepairRecordParser(),
        parser_id=REPAIR_PARSER_ID,
    )


__all__ = [
    "REPAIR_PARSER_ID",
    "RepairCapabilityPack",
    "get_repair_capability_pack",
]
