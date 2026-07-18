"""Generic capability registry for production DI (E5)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aiodoo_validation.capabilities.contract import RegisteredCapabilityPack
from aiodoo_validation.exceptions import AiodooValidationError


class CapabilityRegistryError(AiodooValidationError):
    """Raised when capability registration or lookup fails."""


@dataclass
class CapabilityRegistry:
    """Lookup capability packs by capability id (profile name)."""

    _packs: dict[str, RegisteredCapabilityPack] = field(default_factory=dict)

    def register(self, pack: RegisteredCapabilityPack) -> None:
        capability_id = pack.capability_id
        if not capability_id.strip():
            raise CapabilityRegistryError("capability_id must be non-empty.")
        if pack.parser_id != pack.specification.parser_id:
            raise CapabilityRegistryError(
                f"parser_id mismatch for {capability_id!r}: "
                f"pack={pack.parser_id!r} spec={pack.specification.parser_id!r}."
            )
        if capability_id in self._packs:
            raise CapabilityRegistryError(f"Capability {capability_id!r} is already registered.")
        self._packs[capability_id] = pack

    def get(self, capability_id: str) -> RegisteredCapabilityPack:
        pack = self._packs.get(capability_id)
        if pack is None:
            raise CapabilityRegistryError(f"Capability {capability_id!r} is not registered.")
        return pack

    def get_optional(self, capability_id: str) -> RegisteredCapabilityPack | None:
        return self._packs.get(capability_id)

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._packs))


__all__ = [
    "CapabilityRegistry",
    "CapabilityRegistryError",
]
