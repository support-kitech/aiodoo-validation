"""Behavior-gated certification policy — consumes ScoreResult signals (E8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.certification.criteria import (
    CertificationCriteria,
    default_behavior_gated_certification_criteria,
    evaluate_certification_criteria,
)
from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_BEHAVIOR,
    PLANNER_CERTIFICATION_BEHAVIOR,
    REPAIR_CERTIFICATION_BEHAVIOR,
)
from aiodoo_validation.certification.score_signals import (
    extract_behavioral_score_signals,
    find_score_result,
)
from aiodoo_validation.domain.certification import (
    CertificationCapability,
    CertificationContext,
    CertificationMetadata,
    CertificationResult,
)
from aiodoo_validation.domain.enums import ValidationKind
from aiodoo_validation.execution import certification_label, is_framework_only_tier
from aiodoo_validation.scoring.ids import (
    CODING_SCORE_BEHAVIOR,
    PLANNER_SCORE_BEHAVIOR,
    REPAIR_SCORE_BEHAVIOR,
)


def _metadata(
    *,
    policy_id: str,
    name: str,
    source_benchmark_policy_id: str,
    supported_profile: str,
) -> CertificationMetadata:
    return CertificationMetadata(
        policy_id=policy_id,
        name=name,
        description=(
            f"Behavior-gated certification for {source_benchmark_policy_id} "
            "(consumes ScoreResult signals)."
        ),
        version="1.0.0",
        supported_profile=supported_profile,
        source_benchmark_policy_id=source_benchmark_policy_id,
        capabilities=CertificationCapability(
            placeholder=False,
            consumes_benchmark_result=True,
            inspects_filesystem=False,
            applies_thresholds=True,
        ),
    )


@dataclass(frozen=True, slots=True)
class BehaviorGatedCertificationPolicy:
    """
    Certify from behavioral ScoreResult signals via CertificationCriteria.

    Does not inspect oracle metadata, re-run behavior, or re-score.
    """

    metadata: CertificationMetadata
    source_score_policy_id: str
    criteria: CertificationCriteria = field(
        default_factory=default_behavior_gated_certification_criteria
    )

    @classmethod
    def create_for_repair(
        cls,
        *,
        criteria: CertificationCriteria | None = None,
    ) -> BehaviorGatedCertificationPolicy:
        return cls(
            metadata=_metadata(
                policy_id=REPAIR_CERTIFICATION_BEHAVIOR,
                name="Repair Behavior Certification",
                source_benchmark_policy_id="repair.benchmark.behavior",
                supported_profile="repair",
            ),
            source_score_policy_id=REPAIR_SCORE_BEHAVIOR,
            criteria=criteria or default_behavior_gated_certification_criteria(),
        )

    @classmethod
    def create_for_coding(
        cls,
        *,
        criteria: CertificationCriteria | None = None,
    ) -> BehaviorGatedCertificationPolicy:
        return cls(
            metadata=_metadata(
                policy_id=CODING_CERTIFICATION_BEHAVIOR,
                name="Coding Behavior Certification",
                source_benchmark_policy_id="coding.benchmark.behavior",
                supported_profile="coding",
            ),
            source_score_policy_id=CODING_SCORE_BEHAVIOR,
            criteria=criteria or default_behavior_gated_certification_criteria(),
        )

    @classmethod
    def create_for_planner(
        cls,
        *,
        criteria: CertificationCriteria | None = None,
    ) -> BehaviorGatedCertificationPolicy:
        return cls(
            metadata=_metadata(
                policy_id=PLANNER_CERTIFICATION_BEHAVIOR,
                name="Planner Behavior Certification",
                source_benchmark_policy_id="planner.benchmark.behavior",
                supported_profile="planner",
            ),
            source_score_policy_id=PLANNER_SCORE_BEHAVIOR,
            criteria=criteria or default_behavior_gated_certification_criteria(),
        )

    def certify(self, context: CertificationContext) -> CertificationResult:
        started = perf_counter()
        bench = context.benchmark_result
        score = find_score_result(context.score_execution, self.source_score_policy_id)

        if score is None:
            evaluation = evaluate_certification_criteria(
                self.criteria,
                execution_tier=context.execution_tier,
                behavior_pass=None,
                behavior_deferred=False,
                benchmark_pass=bool(bench.benchmark_pass),
                behavior_score=None,
                transform_score=None,
                weighted_score=None,
                benchmark_score=float(bench.benchmark_score),
                validation_kind=ValidationKind.BEHAVIORAL,
            )
        else:
            signals = extract_behavioral_score_signals(score)
            evaluation = evaluate_certification_criteria(
                self.criteria,
                execution_tier=context.execution_tier,
                behavior_pass=signals.behavior_pass,
                behavior_deferred=signals.deferred,
                benchmark_pass=bool(bench.benchmark_pass),
                behavior_score=signals.behavior_score,
                transform_score=signals.transform_score,
                weighted_score=signals.weighted_score,
                benchmark_score=float(bench.benchmark_score),
                validation_kind=ValidationKind.BEHAVIORAL,
            )

        duration_ms = max(0, int((perf_counter() - started) * 1000))
        label = certification_label(
            profile_name=context.profile_name,
            certified=evaluation.certified,
        )
        if is_framework_only_tier(context.execution_tier):
            message = "Standard tier never production-certifies."
        elif evaluation.certified:
            message = f"Behavior certification granted ({label})."
        else:
            message = f"Behavior certification denied ({label}): " + ", ".join(evaluation.reasons)

        return CertificationResult(
            policy_id=self.metadata.policy_id,
            source_benchmark_policy_id=self.metadata.source_benchmark_policy_id,
            success=True,
            certified=evaluation.certified,
            certification_score=(float(bench.benchmark_score) if evaluation.certified else 0.0),
            certification_level="PASS" if evaluation.certified else "NOT_CERTIFIED",
            message=message,
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "framework_only": is_framework_only_tier(context.execution_tier),
                    "certification_label": label,
                    "criteria_reasons": evaluation.reasons,
                    "criteria_signals": dict(evaluation.signals),
                    "validation_kind": ValidationKind.BEHAVIORAL.value,
                    "source_score_policy_id": self.source_score_policy_id,
                    "benchmark_pass": bool(bench.benchmark_pass),
                    "benchmark_score": float(bench.benchmark_score),
                    "behavior_gated": True,
                }
            ),
        )


__all__ = [
    "BehaviorGatedCertificationPolicy",
]
