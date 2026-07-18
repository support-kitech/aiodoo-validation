"""Capability packs — profile-local parsers and declarative metadata."""

from aiodoo_validation.capabilities.bootstrap import (
    create_default_capability_registry,
    register_builtin_capability_packs,
)
from aiodoo_validation.capabilities.contract import (
    CapabilityRecordParser,
    RegisteredCapabilityPack,
)
from aiodoo_validation.capabilities.registry import (
    CapabilityRegistry,
    CapabilityRegistryError,
)
from aiodoo_validation.capabilities.repair import (
    REPAIR_PARSER_ID,
    RepairCapabilityPack,
    RepairParseError,
    RepairRecordParser,
    get_repair_capability_pack,
)

__all__ = [
    "REPAIR_PARSER_ID",
    "CapabilityRecordParser",
    "CapabilityRegistry",
    "CapabilityRegistryError",
    "RegisteredCapabilityPack",
    "RepairCapabilityPack",
    "RepairParseError",
    "RepairRecordParser",
    "create_default_capability_registry",
    "get_repair_capability_pack",
    "register_builtin_capability_packs",
]
