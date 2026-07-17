"""Placeholder oracle implementations (Phase 5 — no real validation logic)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.oracle import (
    OracleCapability,
    OracleContext,
    OracleMetadata,
    OracleResult,
)
from aiodoo_validation.oracles.ids import (
    CODING_ORACLE_MANIFEST,
    CODING_ORACLE_METADATA,
    CODING_ORACLE_MODULE_STRUCTURE,
    CODING_ORACLE_PYTHON,
    CODING_ORACLE_SECURITY,
    CODING_ORACLE_XML,
)


def placeholder_metadata(
    *,
    oracle_id: str,
    name: str,
    description: str,
    supported_profile: str = "coding",
    version: str = "0.0.0-placeholder",
) -> OracleMetadata:
    return OracleMetadata(
        oracle_id=oracle_id,
        name=name,
        description=description,
        version=version,
        supported_profile=supported_profile,
        capabilities=OracleCapability(
            placeholder=True,
            reads_artifacts=False,
            uses_inference=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class PlaceholderOracle:
    """Base placeholder oracle that always succeeds without inspecting artifacts."""

    metadata: OracleMetadata

    def execute(self, context: OracleContext) -> OracleResult:
        started = perf_counter()
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return OracleResult(
            oracle_id=self.metadata.oracle_id,
            success=True,
            message=f"Placeholder oracle {self.metadata.oracle_id!r} executed.",
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": True,
                    "profile_name": context.profile_name,
                    "plan_digest": context.plan_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class MetadataOracle(PlaceholderOracle):
    """Placeholder metadata validation oracle."""

    @staticmethod
    def create() -> MetadataOracle:
        return MetadataOracle(
            metadata=placeholder_metadata(
                oracle_id=CODING_ORACLE_METADATA,
                name="Metadata Oracle",
                description="Placeholder metadata validation oracle.",
            )
        )


@dataclass(frozen=True, slots=True)
class ManifestOracle(PlaceholderOracle):
    """Placeholder Odoo manifest validation oracle."""

    @staticmethod
    def create() -> ManifestOracle:
        return ManifestOracle(
            metadata=placeholder_metadata(
                oracle_id=CODING_ORACLE_MANIFEST,
                name="Manifest Oracle",
                description="Placeholder Odoo manifest validation oracle.",
            )
        )


@dataclass(frozen=True, slots=True)
class PythonOracle(PlaceholderOracle):
    """Placeholder Python source validation oracle."""

    @staticmethod
    def create() -> PythonOracle:
        return PythonOracle(
            metadata=placeholder_metadata(
                oracle_id=CODING_ORACLE_PYTHON,
                name="Python Oracle",
                description="Placeholder Python source validation oracle.",
            )
        )


@dataclass(frozen=True, slots=True)
class XmlOracle(PlaceholderOracle):
    """Placeholder XML view validation oracle."""

    @staticmethod
    def create() -> XmlOracle:
        return XmlOracle(
            metadata=placeholder_metadata(
                oracle_id=CODING_ORACLE_XML,
                name="XML Oracle",
                description="Placeholder XML view validation oracle.",
            )
        )


@dataclass(frozen=True, slots=True)
class SecurityOracle(PlaceholderOracle):
    """Placeholder security validation oracle."""

    @staticmethod
    def create() -> SecurityOracle:
        return SecurityOracle(
            metadata=placeholder_metadata(
                oracle_id=CODING_ORACLE_SECURITY,
                name="Security Oracle",
                description="Placeholder security validation oracle.",
            )
        )


@dataclass(frozen=True, slots=True)
class ModuleStructureOracle(PlaceholderOracle):
    """Placeholder module structure validation oracle."""

    @staticmethod
    def create() -> ModuleStructureOracle:
        return ModuleStructureOracle(
            metadata=placeholder_metadata(
                oracle_id=CODING_ORACLE_MODULE_STRUCTURE,
                name="Module Structure Oracle",
                description="Placeholder module structure validation oracle.",
            )
        )


def default_coding_placeholder_oracles() -> tuple[PlaceholderOracle, ...]:
    return (
        MetadataOracle.create(),
        ManifestOracle.create(),
        PythonOracle.create(),
        XmlOracle.create(),
        SecurityOracle.create(),
        ModuleStructureOracle.create(),
    )
