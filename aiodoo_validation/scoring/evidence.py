"""Interpret behavioral oracle evidence for scoring (E6).

Scoring consumes evidence. It never produces transform or behavior results.
OracleResult.metadata remains the transport; this module centralizes parsing so
policies do not each re-implement metadata key semantics.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ValidationKind
from aiodoo_validation.domain.oracle import OracleResult

# Spec / CapabilitySpecification dimension names (extras + first-class fields).
DIM_TRANSFORM_CORRECTNESS = "transform_correctness"
DIM_SYNTAX = "syntax"
DIM_MINIMAL_CHANGE = "minimal_change"
DIM_INTENT_PRESERVATION = "intent_preservation"
DIM_HALLUCINATION = "hallucination"
DIM_EXPLANATION = "explanation"
DIM_SAFETY = "safety"
DIM_BEHAVIOR = "behavior"

_HALLUCINATION_FINDING_MARKERS = frozenset(
    {
        "search_not_found",
        "path_not_found",
        "hallucination",
    }
)


@dataclass(frozen=True, slots=True)
class BehavioralOracleEvidence:
    """
    Normalized view of behavioral OracleResult evidence.

    Optional floats are ``None`` when the oracle did not supply evidence for
    that dimension (defer the dimension — do not invent zero).
    """

    deferred: bool
    validation_kind: str
    capability_id: str | None
    transforms_passed: bool | None
    transform_case_count: int | None
    case_count: int | None
    pass_count: int | None
    fail_count: int | None
    pass_rate: float | None
    transform_correctness: float | None
    behavior: float | None
    hallucination: float | None
    syntax: float | None
    minimal_change: float | None
    intent_preservation: float | None
    explanation: float | None
    safety: float | None
    findings: tuple[str, ...]
    raw_metadata: Mapping[str, Any]

    def dimension_values(self) -> Mapping[str, float | None]:
        """Map Spec dimension names to scored values (``None`` = missing)."""
        return MappingProxyType(
            {
                DIM_TRANSFORM_CORRECTNESS: self.transform_correctness,
                DIM_BEHAVIOR: self.behavior,
                DIM_SYNTAX: self.syntax,
                DIM_MINIMAL_CHANGE: self.minimal_change,
                DIM_INTENT_PRESERVATION: self.intent_preservation,
                DIM_HALLUCINATION: self.hallucination,
                DIM_EXPLANATION: self.explanation,
                DIM_SAFETY: self.safety,
            }
        )


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return None


def _as_non_negative_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _as_pass_rate(value: Any) -> float | None:
    if value is None:
        return None
    try:
        rate = float(value)
    except (TypeError, ValueError):
        return None
    if rate < 0.0 or rate > 100.0:
        return None
    return rate


def _binary_score(passed: bool | None) -> float | None:
    if passed is None:
        return None
    return 100.0 if passed else 0.0


def _pass_rate_from_counts(
    *,
    pass_count: int | None,
    case_count: int | None,
) -> float | None:
    if pass_count is None or case_count is None or case_count <= 0:
        return None
    return 100.0 * float(pass_count) / float(case_count)


def _hallucination_from_findings(findings: tuple[str, ...]) -> float | None:
    """
    Score hallucination only when findings carry an explicit signal.

    E5 provenance typically emits ``transform:pass/fail`` without search/path
    markers. Without markers, return ``None`` (do not invent a score).
    """
    lowered = tuple(item.lower() for item in findings)
    if any(marker in finding for finding in lowered for marker in _HALLUCINATION_FINDING_MARKERS):
        return 0.0
    return None


def interpret_behavioral_oracle_evidence(
    oracle_result: OracleResult,
) -> BehavioralOracleEvidence:
    """Parse OracleResult metadata + findings into scoring evidence."""
    meta = dict(oracle_result.metadata)
    findings = tuple(oracle_result.findings)
    deferred = bool(meta.get("deferred", False))
    kind = str(meta.get("validation_kind", ValidationKind.BEHAVIORAL.value))
    capability_id = meta.get("capability_id")
    capability = str(capability_id) if capability_id is not None else None

    transforms_passed = _as_bool(meta.get("transforms_passed"))
    transform_case_count = _as_non_negative_int(meta.get("transform_case_count"))
    case_count = _as_non_negative_int(meta.get("case_count"))
    pass_count = _as_non_negative_int(meta.get("pass_count"))
    fail_count = _as_non_negative_int(meta.get("fail_count"))

    pass_rate = _as_pass_rate(meta.get("pass_rate"))
    if pass_rate is None:
        pass_rate = _pass_rate_from_counts(
            pass_count=pass_count,
            case_count=case_count,
        )

    # Behavior suite deferred → do not treat missing suite counts as 0%.
    behavior: float | None
    if deferred and pass_rate is None:
        behavior = None
    else:
        behavior = pass_rate

    return BehavioralOracleEvidence(
        deferred=deferred,
        validation_kind=kind,
        capability_id=capability,
        transforms_passed=transforms_passed,
        transform_case_count=transform_case_count,
        case_count=case_count,
        pass_count=pass_count,
        fail_count=fail_count,
        pass_rate=pass_rate,
        transform_correctness=_binary_score(transforms_passed),
        behavior=behavior,
        hallucination=_hallucination_from_findings(findings),
        syntax=None,
        minimal_change=None,
        intent_preservation=None,
        explanation=None,
        safety=None,
        findings=findings,
        raw_metadata=MappingProxyType(meta),
    )


__all__ = [
    "DIM_BEHAVIOR",
    "DIM_EXPLANATION",
    "DIM_HALLUCINATION",
    "DIM_INTENT_PRESERVATION",
    "DIM_MINIMAL_CHANGE",
    "DIM_SAFETY",
    "DIM_SYNTAX",
    "DIM_TRANSFORM_CORRECTNESS",
    "BehavioralOracleEvidence",
    "interpret_behavioral_oracle_evidence",
]
