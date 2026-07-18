"""
Frozen Oracle ID convention (Phase 5 refinement).

Format: ``{profile}.oracle.{name}``

Examples
--------
coding.oracle.metadata
coding.oracle.manifest
coding.oracle.python
coding.oracle.xml
coding.oracle.security
coding.oracle.module_structure
coding.oracle.quality

These IDs are stable across phases. Do not rename them. Future profiles must
use ``{profile}.oracle.{name}`` and must not collide with coding IDs.
"""

from __future__ import annotations

CODING_ORACLE_METADATA = "coding.oracle.metadata"
CODING_ORACLE_MANIFEST = "coding.oracle.manifest"
CODING_ORACLE_PYTHON = "coding.oracle.python"
CODING_ORACLE_XML = "coding.oracle.xml"
CODING_ORACLE_SECURITY = "coding.oracle.security"
CODING_ORACLE_MODULE_STRUCTURE = "coding.oracle.module_structure"
CODING_ORACLE_QUALITY = "coding.oracle.quality"
CODING_ORACLE_BEHAVIOR = "coding.oracle.behavior.coding"

# Registered and executed by default in Phase 5 placeholders (+ behavior).
CODING_ORACLE_IDS_ENABLED: tuple[str, ...] = (
    CODING_ORACLE_METADATA,
    CODING_ORACLE_MANIFEST,
    CODING_ORACLE_PYTHON,
    CODING_ORACLE_XML,
    CODING_ORACLE_SECURITY,
    CODING_ORACLE_MODULE_STRUCTURE,
    CODING_ORACLE_BEHAVIOR,
)

# Declared in the Coding Profile pipeline (quality remains disabled / future).
CODING_ORACLE_IDS_ALL: tuple[str, ...] = (
    *CODING_ORACLE_IDS_ENABLED,
    CODING_ORACLE_QUALITY,
)

CODING_ORACLE_ID_SET: frozenset[str] = frozenset(CODING_ORACLE_IDS_ALL)
