"""Extract certification signals from ScoreResult only (E8).

Never reads OracleResult metadata. Never re-runs behavior or scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiodoo_validation.domain.scoring import ScoreExecutionResult, ScoreResult


@dataclass(frozen=True, slots=True)
class BehavioralScoreSignals:
    """Behavioral certification signals derived from a ScoreResult."""

    deferred: bool
    behavior_pass: bool | None
    behavior_score: float | None
    transform_score: float | None
    weighted_score: float | None
    source_policy_id: str


def find_score_result(
    execution: ScoreExecutionResult | None,
    policy_id: str,
) -> ScoreResult | None:
    """Locate a ScoreResult by policy id within a score execution."""
    if execution is None:
        return None
    for result in execution.results:
        if result.policy_id == policy_id:
            return result
    return None


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_behavioral_score_signals(score: ScoreResult) -> BehavioralScoreSignals:
    """
    Derive behavior/transform signals from a behavioral ScoreResult.

    Expects metadata produced by behavioral scoring policies (E6), especially:
    ``deferred``, ``dimensions.behavior``, ``dimensions.extras.transform_correctness``,
    ``dimensions.weighted``, and optional ``pass_rate``.
    """
    meta = dict(score.metadata)
    deferred = bool(meta.get("deferred", False))
    dims_raw = meta.get("dimensions")
    dims: dict[str, Any] = dims_raw if isinstance(dims_raw, dict) else {}
    extras_raw = dims.get("extras")
    extras: dict[str, Any] = extras_raw if isinstance(extras_raw, dict) else {}

    behavior_score = _as_optional_float(dims.get("behavior"))
    if behavior_score is None:
        behavior_score = _as_optional_float(meta.get("pass_rate"))

    transform_score = _as_optional_float(extras.get("transform_correctness"))
    if transform_score is None:
        evidence_raw = meta.get("evidence_dimensions")
        if isinstance(evidence_raw, dict):
            transform_score = _as_optional_float(evidence_raw.get("transform_correctness"))

    weighted_score = _as_optional_float(dims.get("weighted"))
    if weighted_score is None:
        weighted_score = _as_optional_float(score.score)

    if deferred:
        behavior_pass: bool | None = None
    elif behavior_score is None:
        behavior_pass = None
    else:
        behavior_pass = behavior_score >= 100.0

    return BehavioralScoreSignals(
        deferred=deferred,
        behavior_pass=behavior_pass,
        behavior_score=behavior_score,
        transform_score=transform_score,
        weighted_score=weighted_score,
        source_policy_id=score.policy_id,
    )


__all__ = [
    "BehavioralScoreSignals",
    "extract_behavioral_score_signals",
    "find_score_result",
]
