"""
Frozen Scoring Policy ID convention (Phase 6).

Format: ``{profile}.score.{name}``

Each policy scores exactly one OracleResult identified by the matching
``{profile}.oracle.{name}`` ID (see ``oracles.ids``).
"""

from __future__ import annotations

from aiodoo_validation.oracles.ids import (
    CODING_ORACLE_BEHAVIOR,
    CODING_ORACLE_MANIFEST,
    CODING_ORACLE_METADATA,
    CODING_ORACLE_MODULE_STRUCTURE,
    CODING_ORACLE_PYTHON,
    CODING_ORACLE_QUALITY,
    CODING_ORACLE_SECURITY,
    CODING_ORACLE_XML,
)

CODING_SCORE_METADATA = "coding.score.metadata"
CODING_SCORE_MANIFEST = "coding.score.manifest"
CODING_SCORE_PYTHON = "coding.score.python"
CODING_SCORE_XML = "coding.score.xml"
CODING_SCORE_SECURITY = "coding.score.security"
CODING_SCORE_MODULE_STRUCTURE = "coding.score.module_structure"
CODING_SCORE_QUALITY = "coding.score.quality"
CODING_SCORE_BEHAVIOR = "coding.score.behavior"

CODING_SCORE_IDS_ENABLED: tuple[str, ...] = (
    CODING_SCORE_METADATA,
    CODING_SCORE_MANIFEST,
    CODING_SCORE_PYTHON,
    CODING_SCORE_XML,
    CODING_SCORE_SECURITY,
    CODING_SCORE_MODULE_STRUCTURE,
    CODING_SCORE_BEHAVIOR,
)

CODING_SCORE_IDS_ALL: tuple[str, ...] = (
    *CODING_SCORE_IDS_ENABLED,
    CODING_SCORE_QUALITY,
)

# policy_id → source oracle_id
CODING_SCORE_TO_ORACLE: dict[str, str] = {
    CODING_SCORE_METADATA: CODING_ORACLE_METADATA,
    CODING_SCORE_MANIFEST: CODING_ORACLE_MANIFEST,
    CODING_SCORE_PYTHON: CODING_ORACLE_PYTHON,
    CODING_SCORE_XML: CODING_ORACLE_XML,
    CODING_SCORE_SECURITY: CODING_ORACLE_SECURITY,
    CODING_SCORE_MODULE_STRUCTURE: CODING_ORACLE_MODULE_STRUCTURE,
    CODING_SCORE_QUALITY: CODING_ORACLE_QUALITY,
    CODING_SCORE_BEHAVIOR: CODING_ORACLE_BEHAVIOR,
}

PLACEHOLDER_SCORE_VALUE = 100.0

# Repair behavioral scoring (E6) — source oracle: repair.oracle.behavior.repair
REPAIR_SCORE_BEHAVIOR = "repair.score.behavior"
REPAIR_SCORE_TO_ORACLE: dict[str, str] = {
    REPAIR_SCORE_BEHAVIOR: "repair.oracle.behavior.repair",
}
