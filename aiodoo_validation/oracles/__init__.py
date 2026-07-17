"""Oracle Framework package (Phase 5)."""

from aiodoo_validation.oracles.base import Oracle
from aiodoo_validation.oracles.engine import OracleEngine
from aiodoo_validation.oracles.ids import (
    CODING_ORACLE_IDS_ALL,
    CODING_ORACLE_IDS_ENABLED,
    CODING_ORACLE_MANIFEST,
    CODING_ORACLE_METADATA,
    CODING_ORACLE_MODULE_STRUCTURE,
    CODING_ORACLE_PYTHON,
    CODING_ORACLE_QUALITY,
    CODING_ORACLE_SECURITY,
    CODING_ORACLE_XML,
)
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
    "CODING_ORACLE_IDS_ALL",
    "CODING_ORACLE_IDS_ENABLED",
    "CODING_ORACLE_MANIFEST",
    "CODING_ORACLE_METADATA",
    "CODING_ORACLE_MODULE_STRUCTURE",
    "CODING_ORACLE_PYTHON",
    "CODING_ORACLE_QUALITY",
    "CODING_ORACLE_SECURITY",
    "CODING_ORACLE_XML",
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
