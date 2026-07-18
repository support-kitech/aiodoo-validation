"""Evaluation capability pack registration (pack-local; behavioral DI is later)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.capabilities.evaluation.parser import EvaluationRecordParser
from aiodoo_validation.capabilities.evaluation.specification import (
    EVALUATION_PARSER_ID,
    build_evaluation_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


@dataclass(frozen=True, slots=True)
class EvaluationCapabilityPack:
    """
    Registered Evaluation capability surface for Capability Delivery.

    Pack registration is foundation (Phase 1). Behavioral oracle wiring is
    Behavioral production wiring registers alongside Repair, Coding, and Planner.
    """

    specification: CapabilitySpecification
    parser: EvaluationRecordParser
    parser_id: str = EVALUATION_PARSER_ID

    @property
    def capability_id(self) -> str:
        return self.specification.id

    def capability_yaml(self) -> str:
        """Return declarative capability.yaml text."""
        return capability_yaml_path().read_text(encoding="utf-8")


def get_evaluation_capability_pack() -> EvaluationCapabilityPack:
    """Return the Evaluation pack registration (specification + parser)."""
    specification = build_evaluation_specification()
    if specification.parser_id != EVALUATION_PARSER_ID:
        raise RuntimeError("Evaluation specification parser_id mismatch.")
    return EvaluationCapabilityPack(
        specification=specification,
        parser=EvaluationRecordParser(),
        parser_id=EVALUATION_PARSER_ID,
    )


__all__ = [
    "EVALUATION_PARSER_ID",
    "EvaluationCapabilityPack",
    "get_evaluation_capability_pack",
]
