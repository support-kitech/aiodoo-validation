"""
Frozen Certification Policy ID convention (Phase 8).

Format: ``{profile}.certification.{name}``

Each policy certifies exactly one BenchmarkResult identified by the matching
``{profile}.benchmark.{name}`` ID (see ``benchmark.ids``).
"""

from __future__ import annotations

from aiodoo_validation.benchmark.ids import (
    CODING_BENCHMARK_BEHAVIOR,
    CODING_BENCHMARK_MANIFEST,
    CODING_BENCHMARK_METADATA,
    CODING_BENCHMARK_MODULE_STRUCTURE,
    CODING_BENCHMARK_PYTHON,
    CODING_BENCHMARK_QUALITY,
    CODING_BENCHMARK_SECURITY,
    CODING_BENCHMARK_XML,
)

CODING_CERTIFICATION_METADATA = "coding.certification.metadata"
CODING_CERTIFICATION_MANIFEST = "coding.certification.manifest"
CODING_CERTIFICATION_PYTHON = "coding.certification.python"
CODING_CERTIFICATION_XML = "coding.certification.xml"
CODING_CERTIFICATION_SECURITY = "coding.certification.security"
CODING_CERTIFICATION_MODULE_STRUCTURE = "coding.certification.module_structure"
CODING_CERTIFICATION_QUALITY = "coding.certification.quality"
CODING_CERTIFICATION_BEHAVIOR = "coding.certification.behavior"

CODING_CERTIFICATION_IDS_ENABLED: tuple[str, ...] = (
    CODING_CERTIFICATION_METADATA,
    CODING_CERTIFICATION_MANIFEST,
    CODING_CERTIFICATION_PYTHON,
    CODING_CERTIFICATION_XML,
    CODING_CERTIFICATION_SECURITY,
    CODING_CERTIFICATION_MODULE_STRUCTURE,
    CODING_CERTIFICATION_BEHAVIOR,
)

CODING_CERTIFICATION_IDS_ALL: tuple[str, ...] = (
    *CODING_CERTIFICATION_IDS_ENABLED,
    CODING_CERTIFICATION_QUALITY,
)

# policy_id → source benchmark policy_id
CODING_CERTIFICATION_TO_BENCHMARK: dict[str, str] = {
    CODING_CERTIFICATION_METADATA: CODING_BENCHMARK_METADATA,
    CODING_CERTIFICATION_MANIFEST: CODING_BENCHMARK_MANIFEST,
    CODING_CERTIFICATION_PYTHON: CODING_BENCHMARK_PYTHON,
    CODING_CERTIFICATION_XML: CODING_BENCHMARK_XML,
    CODING_CERTIFICATION_SECURITY: CODING_BENCHMARK_SECURITY,
    CODING_CERTIFICATION_MODULE_STRUCTURE: CODING_BENCHMARK_MODULE_STRUCTURE,
    CODING_CERTIFICATION_QUALITY: CODING_BENCHMARK_QUALITY,
    CODING_CERTIFICATION_BEHAVIOR: CODING_BENCHMARK_BEHAVIOR,
}

PLACEHOLDER_CERTIFIED = True
PLACEHOLDER_CERTIFICATION_SCORE = 100.0
PLACEHOLDER_CERTIFICATION_LEVEL = "PASS"

# Repair behavior-gated certification (E8)
REPAIR_CERTIFICATION_BEHAVIOR = "repair.certification.behavior"
REPAIR_CERTIFICATION_TO_BENCHMARK: dict[str, str] = {
    REPAIR_CERTIFICATION_BEHAVIOR: "repair.benchmark.behavior",
}

# Planner behavior-gated certification
PLANNER_CERTIFICATION_BEHAVIOR = "planner.certification.behavior"
PLANNER_CERTIFICATION_TO_BENCHMARK: dict[str, str] = {
    PLANNER_CERTIFICATION_BEHAVIOR: "planner.benchmark.behavior",
}

# Conversation behavior-gated certification
CONVERSATION_CERTIFICATION_BEHAVIOR = "conversation.certification.behavior"
CONVERSATION_CERTIFICATION_TO_BENCHMARK: dict[str, str] = {
    CONVERSATION_CERTIFICATION_BEHAVIOR: "conversation.benchmark.behavior",
}

# Execution behavior-gated certification
EXECUTION_CERTIFICATION_BEHAVIOR = "execution.certification.behavior"
EXECUTION_CERTIFICATION_TO_BENCHMARK: dict[str, str] = {
    EXECUTION_CERTIFICATION_BEHAVIOR: "execution.benchmark.behavior",
}

# Approval behavior-gated certification
APPROVAL_CERTIFICATION_BEHAVIOR = "approval.certification.behavior"
APPROVAL_CERTIFICATION_TO_BENCHMARK: dict[str, str] = {
    APPROVAL_CERTIFICATION_BEHAVIOR: "approval.benchmark.behavior",
}

# Evaluation behavior-gated certification
EVALUATION_CERTIFICATION_BEHAVIOR = "evaluation.certification.behavior"
EVALUATION_CERTIFICATION_TO_BENCHMARK: dict[str, str] = {
    EVALUATION_CERTIFICATION_BEHAVIOR: "evaluation.benchmark.behavior",
}
