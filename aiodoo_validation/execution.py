"""Execution-tier helpers for production validation behavior.

Tiers
-----
standard
    Framework/pipeline validation only.
    Stub inference. Structural oracles may run for wiring checks.
    Never production-certifies.
smoke
    Small real validation depth.
    Real inference (Qwen with mock fallback).
    Structural oracles today; behavioral corpora when available (limited).
    Real scoring / benchmark / certification.
full / prod
    Complete validation depth.
    Real inference.
    Full structural set; full behavioral corpora when available.
    Complete certification.
    ``prod`` is an alias of ``full`` (``full`` retained for compatibility).
"""

from __future__ import annotations

from aiodoo_validation.domain.enums import ExecutionTier

# CLI / request values accepted for the production tier.
PRODUCTION_TIER_ALIASES: frozenset[str] = frozenset({"full", "prod"})

# Soft cap on behavioral cases for smoke when a corpus is attached later.
SMOKE_BEHAVIOR_CASE_LIMIT = 8


def normalize_execution_tier(value: str | ExecutionTier) -> ExecutionTier:
    """Normalize user/CLI tier strings; map ``prod`` → ``full``."""
    if isinstance(value, ExecutionTier):
        raw = value.value
    else:
        raw = str(value).strip().lower()
    if raw in PRODUCTION_TIER_ALIASES:
        return ExecutionTier.FULL
    return ExecutionTier(raw)


def is_framework_only_tier(tier: ExecutionTier | str) -> bool:
    """Return True when the tier must never attempt production certification."""
    return normalize_execution_tier(tier) is ExecutionTier.STANDARD


def allows_certification(tier: ExecutionTier | str) -> bool:
    """Return True when smoke/full may grant profile certification."""
    return not is_framework_only_tier(tier)


def requires_real_inference(tier: ExecutionTier | str) -> bool:
    """Return True when smoke/full should attempt real model load."""
    return normalize_execution_tier(tier) in {ExecutionTier.SMOKE, ExecutionTier.FULL}


def is_smoke_tier(tier: ExecutionTier | str) -> bool:
    return normalize_execution_tier(tier) is ExecutionTier.SMOKE


def is_full_tier(tier: ExecutionTier | str) -> bool:
    return normalize_execution_tier(tier) is ExecutionTier.FULL


def behavior_case_limit(tier: ExecutionTier | str) -> int | None:
    """
    Maximum behavioral cases for the tier.

    Returns ``None`` for full/prod (no soft cap). Returns a small limit for
    smoke. Returns ``0`` for standard (behavioral evaluation is not attempted).
    """
    normalized = normalize_execution_tier(tier)
    if normalized is ExecutionTier.STANDARD:
        return 0
    if normalized is ExecutionTier.SMOKE:
        return SMOKE_BEHAVIOR_CASE_LIMIT
    return None


def certification_label(*, profile_name: str, certified: bool) -> str:
    """Profile-driven certification label (e.g. ``coding-certified``)."""
    profile = profile_name.strip().lower() or "unknown"
    return f"{profile}-certified" if certified else f"{profile}-not-certified"


__all__ = [
    "PRODUCTION_TIER_ALIASES",
    "SMOKE_BEHAVIOR_CASE_LIMIT",
    "allows_certification",
    "behavior_case_limit",
    "certification_label",
    "is_framework_only_tier",
    "is_full_tier",
    "is_smoke_tier",
    "normalize_execution_tier",
    "requires_real_inference",
]
