"""Validation request domain model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ExecutionTier, OdooVersion, SupportedValidationProfile
from aiodoo_validation.exceptions import InvalidRequestError

SUPPORTED_PROTOCOL_MAJOR = 1
SUPPORTED_PROFILES = frozenset({SupportedValidationProfile.CODING.value})
SUPPORTED_ODOO_VERSIONS = frozenset({17, 18, 19})


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    """
    Immutable validation request.

    Fields align with frozen TDD request metadata. Paths are opaque strings in
    Phase 0/1 — no artifact loading occurs.
    """

    profile_name: str
    base_model_ref: str
    adapter_ref: str
    execution_tier: ExecutionTier = ExecutionTier.STANDARD
    protocol_major: int = SUPPORTED_PROTOCOL_MAJOR
    protocol_minor: int = 0
    odoo_versions: tuple[int, ...] = (OdooVersion.V17, OdooVersion.V18, OdooVersion.V19)
    strict_fingerprint_policy: bool = False
    run_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.profile_name.strip():
            raise InvalidRequestError("profile_name must be non-empty.")
        if self.profile_name not in SUPPORTED_PROFILES:
            raise InvalidRequestError(
                f"Unsupported profile_name {self.profile_name!r}. "
                f"Supported: {sorted(SUPPORTED_PROFILES)}."
            )
        if not self.base_model_ref.strip():
            raise InvalidRequestError("base_model_ref must be non-empty.")
        if not self.adapter_ref.strip():
            raise InvalidRequestError("adapter_ref must be non-empty.")
        if self.protocol_major != SUPPORTED_PROTOCOL_MAJOR:
            raise InvalidRequestError(
                f"Unsupported protocol_major {self.protocol_major}. "
                f"Only Validation Protocol V{SUPPORTED_PROTOCOL_MAJOR} is supported."
            )
        if self.protocol_minor < 0:
            raise InvalidRequestError("protocol_minor must be >= 0.")
        if not self.odoo_versions:
            raise InvalidRequestError("odoo_versions must contain at least one version.")
        for version in self.odoo_versions:
            if version not in SUPPORTED_ODOO_VERSIONS:
                raise InvalidRequestError(
                    f"Unsupported Odoo version {version}. "
                    f"Supported: {sorted(SUPPORTED_ODOO_VERSIONS)}."
                )
        if not isinstance(self.metadata, Mapping):
            raise InvalidRequestError("metadata must be a mapping.")
