"""Planner capability pack registration (pack-local; behavioral DI is later)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.capabilities.planner.parser import PlannerRecordParser
from aiodoo_validation.capabilities.planner.specification import (
    PLANNER_PARSER_ID,
    build_planner_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


@dataclass(frozen=True, slots=True)
class PlannerCapabilityPack:
    """
    Registered Planner capability surface for Capability Delivery.

    Pack registration is foundation (Phase 1). Behavioral oracle wiring is
    Behavioral production wiring registers alongside Repair and Coding.
    """

    specification: CapabilitySpecification
    parser: PlannerRecordParser
    parser_id: str = PLANNER_PARSER_ID

    @property
    def capability_id(self) -> str:
        return self.specification.id

    def capability_yaml(self) -> str:
        """Return declarative capability.yaml text."""
        return capability_yaml_path().read_text(encoding="utf-8")


def get_planner_capability_pack() -> PlannerCapabilityPack:
    """Return the Planner pack registration (specification + parser)."""
    specification = build_planner_specification()
    if specification.parser_id != PLANNER_PARSER_ID:
        raise RuntimeError("Planner specification parser_id mismatch.")
    return PlannerCapabilityPack(
        specification=specification,
        parser=PlannerRecordParser(),
        parser_id=PLANNER_PARSER_ID,
    )


__all__ = [
    "PLANNER_PARSER_ID",
    "PlannerCapabilityPack",
    "get_planner_capability_pack",
]
