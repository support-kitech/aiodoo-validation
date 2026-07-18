"""Approval capability pack registration (pack-local; behavioral DI is later)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.capabilities.approval.parser import ApprovalRecordParser
from aiodoo_validation.capabilities.approval.specification import (
    APPROVAL_PARSER_ID,
    build_approval_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


@dataclass(frozen=True, slots=True)
class ApprovalCapabilityPack:
    """
    Registered Approval capability surface for Capability Delivery.

    Pack registration is foundation (Phase 1). Behavioral oracle wiring is
    Behavioral production wiring registers alongside Repair, Coding, and Planner.
    """

    specification: CapabilitySpecification
    parser: ApprovalRecordParser
    parser_id: str = APPROVAL_PARSER_ID

    @property
    def capability_id(self) -> str:
        return self.specification.id

    def capability_yaml(self) -> str:
        """Return declarative capability.yaml text."""
        return capability_yaml_path().read_text(encoding="utf-8")


def get_approval_capability_pack() -> ApprovalCapabilityPack:
    """Return the Approval pack registration (specification + parser)."""
    specification = build_approval_specification()
    if specification.parser_id != APPROVAL_PARSER_ID:
        raise RuntimeError("Approval specification parser_id mismatch.")
    return ApprovalCapabilityPack(
        specification=specification,
        parser=ApprovalRecordParser(),
        parser_id=APPROVAL_PARSER_ID,
    )


__all__ = [
    "APPROVAL_PARSER_ID",
    "ApprovalCapabilityPack",
    "get_approval_capability_pack",
]
