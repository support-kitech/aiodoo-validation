"""Execution-tier helpers for production validation behavior.

Tiers
-----
standard
    Framework/pipeline validation only. Never production-certifies.
smoke
    Small real validation (structural oracles + optional real inference).
    May certify when criteria pass.
full / prod
    Full production validation depth. ``prod`` is an alias of ``full`` for
    CLI compatibility (``full`` retained).
"""

from __future__ import annotations

from aiodoo_validation.domain.enums import ExecutionTier

# CLI / request values accepted for the production tier.
PRODUCTION_TIER_ALIASES: frozenset[str] = frozenset({"full", "prod"})


def normalize_execution_tier(value: str | ExecutionTier) -> ExecutionTier:
    """Normalize user/CLI tier strings; map ``prod`` → ``full``."""
    if isinstance(value, ExecutionTier):
        raw = value.value
    else:
        raw = str(value).strip().lower()
    if raw in PRODUCTION_TIER_ALIASES:
        return ExecutionTier.FULL
    return ExecutionTier(raw)


def is_framework_only_tier(tier: ExecutionTier) -> bool:
    """Return True when the tier must never attempt production certification."""
    return normalize_execution_tier(tier) is ExecutionTier.STANDARD


def requires_real_inference(tier: ExecutionTier) -> bool:
    """Return True when smoke/full should attempt real model load."""
    return normalize_execution_tier(tier) in {ExecutionTier.SMOKE, ExecutionTier.FULL}


def certification_label(*, profile_name: str, certified: bool) -> str:
    """Profile-driven certification label (e.g. ``coding-certified``)."""
    profile = profile_name.strip().lower() or "unknown"
    return f"{profile}-certified" if certified else f"{profile}-not-certified"


__all__ = [
    "PRODUCTION_TIER_ALIASES",
    "certification_label",
    "is_framework_only_tier",
    "normalize_execution_tier",
    "requires_real_inference",
]
