"""Version 1 scope constants shared across resolution and inference."""

from __future__ import annotations

from aiodoo_validation.domain.enums import SupportedValidationProfile

SUPPORTED_V1_PROFILES = frozenset({SupportedValidationProfile.CODING.value})
SUPPORTED_V1_ADAPTER_TYPES = frozenset({SupportedValidationProfile.CODING.value})
REJECTED_ADAPTER_TYPES = frozenset({"planner", "repair", "conversation", "execution", "evaluation"})
SUPPORTED_MODEL_FAMILIES = frozenset({"qwen"})
SUPPORTED_MODEL_IDENTIFIERS = frozenset({"qwen3-8b", "qwen/qwen3-8b"})
