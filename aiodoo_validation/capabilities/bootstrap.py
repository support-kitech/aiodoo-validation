"""Explicit builtin capability pack registration (no import-time side effects)."""

from __future__ import annotations

from aiodoo_validation.capabilities.contract import RegisteredCapabilityPack
from aiodoo_validation.capabilities.registry import CapabilityRegistry


def register_builtin_capability_packs(registry: CapabilityRegistry) -> CapabilityRegistry:
    """
    Register shipped capability packs into ``registry``.

    Production imports this bootstrap helper — not pack parser classes.
    """
    from aiodoo_validation.capabilities.coding.registration import (
        get_coding_capability_pack,
    )
    from aiodoo_validation.capabilities.conversation.registration import (
        get_conversation_capability_pack,
    )
    from aiodoo_validation.capabilities.execution.registration import (
        get_execution_capability_pack,
    )
    from aiodoo_validation.capabilities.planner.registration import (
        get_planner_capability_pack,
    )
    from aiodoo_validation.capabilities.repair.registration import (
        get_repair_capability_pack,
    )

    for get_pack in (
        get_coding_capability_pack,
        get_conversation_capability_pack,
        get_execution_capability_pack,
        get_planner_capability_pack,
        get_repair_capability_pack,
    ):
        pack = get_pack()
        registry.register(
            RegisteredCapabilityPack(
                specification=pack.specification,
                parser=pack.parser,
                parser_id=pack.parser_id,
            )
        )
    return registry


def create_default_capability_registry() -> CapabilityRegistry:
    """Create a registry with all builtin capability packs."""
    return register_builtin_capability_packs(CapabilityRegistry())


__all__ = [
    "create_default_capability_registry",
    "register_builtin_capability_packs",
]
