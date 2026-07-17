"""Coding profile policy constants (Phase 4)."""

from __future__ import annotations

from aiodoo_validation.domain.enums import ArtifactType, SupportedValidationProfile

PROFILE_NAME = SupportedValidationProfile.CODING.value

REJECTED_PROFILE_NAMES = frozenset({"planner", "repair", "conversation", "execution", "evaluation"})
SUPPORTED_ADAPTER_TYPES = frozenset({PROFILE_NAME})
SUPPORTED_MODEL_FAMILIES = frozenset({"qwen"})
SUPPORTED_MODEL_IDENTIFIERS = frozenset({"qwen3-8b", "qwen/qwen3-8b"})
SUPPORTED_ARTIFACT_TYPES = frozenset(
    {
        ArtifactType.BASE_MODEL.value,
        ArtifactType.CODING_ADAPTER.value,
        ArtifactType.MERGED_MODEL.value,
    }
)
SUPPORTED_PROTOCOL_MAJORS = frozenset({1})
SUPPORTED_RUNTIMES = frozenset({"mock", "stub", "qwen_hf"})
