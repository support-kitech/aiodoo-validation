"""Conversation capability pack registration (pack-local; behavioral DI is later)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.capabilities.conversation.parser import ConversationRecordParser
from aiodoo_validation.capabilities.conversation.specification import (
    CONVERSATION_PARSER_ID,
    build_conversation_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_spec import CapabilitySpecification


@dataclass(frozen=True, slots=True)
class ConversationCapabilityPack:
    """
    Registered Conversation capability surface for Capability Delivery.

    Pack registration is foundation (Phase 1). Behavioral oracle wiring is
    Behavioral production wiring registers alongside Repair, Coding, and Planner.
    """

    specification: CapabilitySpecification
    parser: ConversationRecordParser
    parser_id: str = CONVERSATION_PARSER_ID

    @property
    def capability_id(self) -> str:
        return self.specification.id

    def capability_yaml(self) -> str:
        """Return declarative capability.yaml text."""
        return capability_yaml_path().read_text(encoding="utf-8")


def get_conversation_capability_pack() -> ConversationCapabilityPack:
    """Return the Conversation pack registration (specification + parser)."""
    specification = build_conversation_specification()
    if specification.parser_id != CONVERSATION_PARSER_ID:
        raise RuntimeError("Conversation specification parser_id mismatch.")
    return ConversationCapabilityPack(
        specification=specification,
        parser=ConversationRecordParser(),
        parser_id=CONVERSATION_PARSER_ID,
    )


__all__ = [
    "CONVERSATION_PARSER_ID",
    "ConversationCapabilityPack",
    "get_conversation_capability_pack",
]
