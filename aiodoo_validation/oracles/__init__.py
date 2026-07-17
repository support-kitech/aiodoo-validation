"""Oracle Framework package (Phase 5)."""

from aiodoo_validation.oracles.base import Oracle
from aiodoo_validation.oracles.engine import OracleEngine
from aiodoo_validation.oracles.placeholders import (
    ManifestOracle,
    MetadataOracle,
    ModuleStructureOracle,
    PlaceholderOracle,
    PythonOracle,
    SecurityOracle,
    XmlOracle,
    placeholder_metadata,
)
from aiodoo_validation.oracles.registry import OracleRegistry

__all__ = [
    "ManifestOracle",
    "MetadataOracle",
    "ModuleStructureOracle",
    "Oracle",
    "OracleEngine",
    "OracleRegistry",
    "PlaceholderOracle",
    "PythonOracle",
    "SecurityOracle",
    "XmlOracle",
    "placeholder_metadata",
]
