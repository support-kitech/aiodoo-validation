"""Inference runtime compatibility policy (Phase 3)."""

from __future__ import annotations

SUPPORTED_RUNTIME_MODEL_FAMILIES = frozenset({"qwen"})
SUPPORTED_RUNTIME_MODEL_IDENTIFIERS = frozenset({"qwen3-8b", "qwen/qwen3-8b"})
