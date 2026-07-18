"""Explicit builtin capability pack registration (no import-time side effects)."""

from __future__ import annotations

from aiodoo_validation.capabilities.contract import RegisteredCapabilityPack
from aiodoo_validation.capabilities.registry import CapabilityRegistry


def register_builtin_capability_packs(registry: CapabilityRegistry) -> CapabilityRegistry:
    """
    Register shipped capability packs into ``registry``.

    Production imports this bootstrap helper — not Repair parser classes.
    """
    from aiodoo_validation.capabilities.repair.registration import (
        get_repair_capability_pack,
    )

    repair = get_repair_capability_pack()
    registry.register(
        RegisteredCapabilityPack(
            specification=repair.specification,
            parser=repair.parser,
            parser_id=repair.parser_id,
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
