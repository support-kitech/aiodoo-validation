"""Immutable repository and protocol metadata (Phase 11)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.__version__ import __version__
from aiodoo_validation.domain.enums import ExecutionTier, ValidationStage
from aiodoo_validation.domain.request import (
    SUPPORTED_ODOO_VERSIONS,
    SUPPORTED_PROFILES,
    SUPPORTED_PROTOCOL_MAJOR,
)
from aiodoo_validation.engine import PIPELINE_STAGE_ORDER

PIPELINE_STAGE_ORDER_PUBLIC: tuple[ValidationStage, ...] = PIPELINE_STAGE_ORDER


@dataclass(frozen=True, slots=True)
class ProtocolInfo:
    """Supported Validation Protocol metadata."""

    major: int
    minor: int

    @property
    def version_label(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass(frozen=True, slots=True)
class RepositoryMetadata:
    """Stable repository metadata for ecosystem consumers."""

    repository_name: str
    repository_version: str
    protocol: ProtocolInfo
    supported_protocols: tuple[ProtocolInfo, ...]
    supported_profiles: tuple[str, ...]
    supported_execution_tiers: tuple[str, ...]
    supported_odoo_versions: tuple[int, ...]
    pipeline_stages: tuple[ValidationStage, ...]


def get_repository_metadata() -> RepositoryMetadata:
    """Return static repository and protocol metadata."""
    protocol = ProtocolInfo(major=SUPPORTED_PROTOCOL_MAJOR, minor=0)
    return RepositoryMetadata(
        repository_name="aiodoo-validation",
        repository_version=__version__,
        protocol=protocol,
        supported_protocols=(protocol,),
        supported_profiles=tuple(sorted(SUPPORTED_PROFILES)),
        supported_execution_tiers=tuple(tier.value for tier in ExecutionTier),
        supported_odoo_versions=tuple(sorted(SUPPORTED_ODOO_VERSIONS)),
        pipeline_stages=PIPELINE_STAGE_ORDER_PUBLIC,
    )
