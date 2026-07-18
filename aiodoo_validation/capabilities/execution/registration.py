"""Execution capability pack registration (pack-local; behavioral DI is later)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.capabilities.execution.parser import ExecutionRecordParser
from aiodoo_validation.capabilities.execution.specification import (
    EXECUTION_PARSER_ID,
    build_execution_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


@dataclass(frozen=True, slots=True)
class ExecutionCapabilityPack:
    """
    Registered Execution capability surface for Capability Delivery.

    Pack registration is foundation (Phase 1). Behavioral oracle wiring is
    Behavioral production wiring registers alongside Repair, Coding, and Planner.
    """

    specification: CapabilitySpecification
    parser: ExecutionRecordParser
    parser_id: str = EXECUTION_PARSER_ID

    @property
    def capability_id(self) -> str:
        return self.specification.id

    def capability_yaml(self) -> str:
        """Return declarative capability.yaml text."""
        return capability_yaml_path().read_text(encoding="utf-8")


def get_execution_capability_pack() -> ExecutionCapabilityPack:
    """Return the Execution pack registration (specification + parser)."""
    specification = build_execution_specification()
    if specification.parser_id != EXECUTION_PARSER_ID:
        raise RuntimeError("Execution specification parser_id mismatch.")
    return ExecutionCapabilityPack(
        specification=specification,
        parser=ExecutionRecordParser(),
        parser_id=EXECUTION_PARSER_ID,
    )


__all__ = [
    "EXECUTION_PARSER_ID",
    "ExecutionCapabilityPack",
    "get_execution_capability_pack",
]
