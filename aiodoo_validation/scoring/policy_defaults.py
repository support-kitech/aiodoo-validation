"""Default behavioral scoring policy data keyed by CapabilitySpecification refs.

Packs own the *reference name* (``default_scoring_policy_ref``). Scoring owns
loading and application. Default weight tables live here because E6 must not
modify capability packs; packs may later ship files that the loader prefers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from aiodoo_validation.scoring.evidence import (
    DIM_BEHAVIOR,
    DIM_EXPLANATION,
    DIM_HALLUCINATION,
    DIM_INTENT_PRESERVATION,
    DIM_MINIMAL_CHANGE,
    DIM_SAFETY,
    DIM_SYNTAX,
    DIM_TRANSFORM_CORRECTNESS,
)

# Matches CapabilitySpecification.default_scoring_policy_ref for Repair.
DEFAULT_BEHAVIORAL_POLICY_REF = "scoring_policy.yaml"


@dataclass(frozen=True, slots=True)
class BehavioralScoringPolicyData:
    """Weights and dimension rules for behavioral score aggregation."""

    policy_ref: str
    weights: Mapping[str, float]
    binary_dimensions: frozenset[str]
    # Missing evidence: skip dimension in weighted aggregate (never invent 0).
    missing_evidence: str = "skip"

    def __post_init__(self) -> None:
        if self.missing_evidence not in {"skip", "zero"}:
            raise ValueError(
                f"missing_evidence must be 'skip' or 'zero', got {self.missing_evidence!r}"
            )
        total = sum(float(weight) for weight in self.weights.values() if float(weight) > 0)
        if total <= 0:
            raise ValueError(f"policy {self.policy_ref!r} requires positive weights")


def _repair_default_policy() -> BehavioralScoringPolicyData:
    """
    Default Repair behavioral weights.

    Transform + behavior dominate because E5 evidence currently supplies those.
    Remaining Spec dimensions keep weight slots so they contribute when evidence
    appears later — without inventing scores today.
    """
    return BehavioralScoringPolicyData(
        policy_ref=DEFAULT_BEHAVIORAL_POLICY_REF,
        weights=MappingProxyType(
            {
                DIM_TRANSFORM_CORRECTNESS: 0.35,
                DIM_BEHAVIOR: 0.25,
                DIM_SYNTAX: 0.10,
                DIM_MINIMAL_CHANGE: 0.10,
                DIM_INTENT_PRESERVATION: 0.05,
                DIM_HALLUCINATION: 0.05,
                DIM_EXPLANATION: 0.05,
                DIM_SAFETY: 0.05,
            }
        ),
        binary_dimensions=frozenset({DIM_TRANSFORM_CORRECTNESS, DIM_SAFETY}),
        missing_evidence="skip",
    )


BEHAVIORAL_SCORING_POLICY_LIBRARY: Mapping[str, BehavioralScoringPolicyData] = MappingProxyType(
    {
        DEFAULT_BEHAVIORAL_POLICY_REF: _repair_default_policy(),
    }
)


__all__ = [
    "BEHAVIORAL_SCORING_POLICY_LIBRARY",
    "DEFAULT_BEHAVIORAL_POLICY_REF",
    "BehavioralScoringPolicyData",
]
