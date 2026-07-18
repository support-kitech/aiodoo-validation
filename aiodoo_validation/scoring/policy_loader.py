"""Load behavioral scoring policy data by CapabilitySpecification ref.

Policy *loading* belongs in ``scoring/``: ScoringEngine applies weights;
CapabilitySpecification only declares ``default_scoring_policy_ref``.

Trade-off vs loading inside ``capabilities/``:
- scoring/: shared loader, no pack import cycle, one place for weight semantics
- capabilities/: pack-owned files closer to Spec ownership of policy *data*

E6 keeps loading in scoring and ships default data for known refs (packs are
frozen this phase). Future phases may resolve pack-local files first.
"""

from __future__ import annotations

from aiodoo_validation.scoring.policy_defaults import (
    BEHAVIORAL_SCORING_POLICY_LIBRARY,
    DEFAULT_BEHAVIORAL_POLICY_REF,
    BehavioralScoringPolicyData,
)


class ScoringPolicyLoadError(LookupError):
    """Raised when a scoring policy ref cannot be resolved."""


def load_behavioral_scoring_policy(
    policy_ref: str | None = None,
) -> BehavioralScoringPolicyData:
    """
    Resolve ``default_scoring_policy_ref`` (or equivalent) to policy data.

    ``None`` or empty uses ``DEFAULT_BEHAVIORAL_POLICY_REF``.
    """
    ref = (policy_ref or DEFAULT_BEHAVIORAL_POLICY_REF).strip()
    if not ref:
        ref = DEFAULT_BEHAVIORAL_POLICY_REF
    try:
        return BEHAVIORAL_SCORING_POLICY_LIBRARY[ref]
    except KeyError as exc:
        known = ", ".join(sorted(BEHAVIORAL_SCORING_POLICY_LIBRARY))
        raise ScoringPolicyLoadError(
            f"Unknown scoring policy ref {ref!r}. Known refs: {known}."
        ) from exc


__all__ = [
    "ScoringPolicyLoadError",
    "load_behavioral_scoring_policy",
]
