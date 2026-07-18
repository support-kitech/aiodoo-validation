"""Behavioral evidence scoring policy (E6).

Consumes OracleResult metadata produced by CapabilityBehavioralOracle.
Does not run BehaviorRunner, TransformationEngine, or CapabilityBehaviorPipeline.
Does not influence certification (E8).
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.enums import ScoreErrorCode, ValidationKind
from aiodoo_validation.domain.scoring import (
    ScoreCapability,
    ScoreContext,
    ScoreError,
    ScoreMetadata,
    ScoreResult,
)
from aiodoo_validation.scoring.dimensions import behavior_dimensions_from_evidence
from aiodoo_validation.scoring.evidence import interpret_behavioral_oracle_evidence
from aiodoo_validation.scoring.ids import (
    CODING_SCORE_BEHAVIOR,
    CODING_SCORE_TO_ORACLE,
    PLANNER_SCORE_BEHAVIOR,
    PLANNER_SCORE_TO_ORACLE,
    REPAIR_SCORE_BEHAVIOR,
    REPAIR_SCORE_TO_ORACLE,
)
from aiodoo_validation.scoring.policy_defaults import (
    DEFAULT_BEHAVIORAL_POLICY_REF,
    BehavioralScoringPolicyData,
)
from aiodoo_validation.scoring.policy_loader import (
    ScoringPolicyLoadError,
    load_behavioral_scoring_policy,
)

SCORING_POLICY_REF_KEY = "scoring_policy_ref"


def _metadata(
    *,
    policy_id: str,
    name: str,
    source_oracle_id: str,
    supported_profile: str,
) -> ScoreMetadata:
    return ScoreMetadata(
        policy_id=policy_id,
        name=name,
        description=(
            f"Behavioral multi-dimension score from oracle {source_oracle_id} "
            f"(policy ref resolved at score time)."
        ),
        version="1.0.0",
        supported_profile=supported_profile,
        source_oracle_id=source_oracle_id,
        capabilities=ScoreCapability(
            placeholder=False,
            consumes_oracle_result=True,
            inspects_filesystem=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class BehavioralEvidenceScorePolicy:
    """
    Aggregate Spec evaluation dimensions from existing behavioral oracle evidence.

    Missing dimensions remain ``None`` and are skipped in the weighted score
    when the loaded policy uses ``missing_evidence='skip'``.
    """

    metadata: ScoreMetadata
    default_policy_ref: str = DEFAULT_BEHAVIORAL_POLICY_REF

    @classmethod
    def create_for_repair(
        cls,
        *,
        policy_ref: str = DEFAULT_BEHAVIORAL_POLICY_REF,
    ) -> BehavioralEvidenceScorePolicy:
        # Validate default ref at construction; score-time overrides may still fail.
        load_behavioral_scoring_policy(policy_ref)
        return cls(
            metadata=_metadata(
                policy_id=REPAIR_SCORE_BEHAVIOR,
                name="Repair Behavior Score",
                source_oracle_id=REPAIR_SCORE_TO_ORACLE[REPAIR_SCORE_BEHAVIOR],
                supported_profile="repair",
            ),
            default_policy_ref=policy_ref,
        )

    @classmethod
    def create_for_coding(
        cls,
        *,
        policy_ref: str = DEFAULT_BEHAVIORAL_POLICY_REF,
    ) -> BehavioralEvidenceScorePolicy:
        load_behavioral_scoring_policy(policy_ref)
        return cls(
            metadata=_metadata(
                policy_id=CODING_SCORE_BEHAVIOR,
                name="Coding Behavior Score",
                source_oracle_id=CODING_SCORE_TO_ORACLE[CODING_SCORE_BEHAVIOR],
                supported_profile="coding",
            ),
            default_policy_ref=policy_ref,
        )

    @classmethod
    def create_for_planner(
        cls,
        *,
        policy_ref: str = DEFAULT_BEHAVIORAL_POLICY_REF,
    ) -> BehavioralEvidenceScorePolicy:
        load_behavioral_scoring_policy(policy_ref)
        return cls(
            metadata=_metadata(
                policy_id=PLANNER_SCORE_BEHAVIOR,
                name="Planner Behavior Score",
                source_oracle_id=PLANNER_SCORE_TO_ORACLE[PLANNER_SCORE_BEHAVIOR],
                supported_profile="planner",
            ),
            default_policy_ref=policy_ref,
        )

    def _resolve_policy(self, context: ScoreContext) -> BehavioralScoringPolicyData:
        configured = context.configuration.get(SCORING_POLICY_REF_KEY)
        ref = str(configured).strip() if configured is not None else self.default_policy_ref
        return load_behavioral_scoring_policy(ref)

    def score(self, context: ScoreContext) -> ScoreResult:
        started = perf_counter()
        try:
            policy = self._resolve_policy(context)
        except ScoringPolicyLoadError as exc:
            duration_ms = max(0, int((perf_counter() - started) * 1000))
            return ScoreResult(
                policy_id=self.metadata.policy_id,
                source_oracle_id=self.metadata.source_oracle_id,
                success=False,
                score=0.0,
                message=str(exc),
                errors=(
                    ScoreError(
                        code=ScoreErrorCode.EXECUTION_FAILURE,
                        message=str(exc),
                        field=SCORING_POLICY_REF_KEY,
                        policy_id=self.metadata.policy_id,
                    ),
                ),
                duration_ms=duration_ms,
                metadata=MappingProxyType(
                    {
                        "placeholder": False,
                        "deferred": False,
                        "policy_load_error": True,
                    }
                ),
            )

        evidence = interpret_behavioral_oracle_evidence(context.oracle_result)
        dimensions = behavior_dimensions_from_evidence(
            evidence=evidence,
            policy=policy,
        )
        weighted = dimensions.weighted
        if weighted is None:
            # Fully missing evidence (typical deferred-without-corpus): score 0.
            score = 0.0
        else:
            score = float(weighted)

        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return ScoreResult(
            policy_id=self.metadata.policy_id,
            source_oracle_id=self.metadata.source_oracle_id,
            success=True,
            score=score,
            message=(
                f"Behavioral score {score:.1f} from oracle "
                f"{context.oracle_result.oracle_id!r} "
                f"(deferred={evidence.deferred}, "
                f"policy={policy.policy_ref!r})."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "oracle_success": bool(context.oracle_result.success),
                    "oracle_duration_ms": context.oracle_result.duration_ms,
                    "deferred": evidence.deferred,
                    "validation_kind": ValidationKind.BEHAVIORAL.value,
                    "capability_id": evidence.capability_id,
                    "scoring_policy_ref": policy.policy_ref,
                    "transforms_passed": evidence.transforms_passed,
                    "pass_rate": evidence.pass_rate,
                    "case_count": evidence.case_count,
                    "pass_count": evidence.pass_count,
                    "fail_count": evidence.fail_count,
                    "dimensions": dict(dimensions.as_mapping()),
                    "evidence_dimensions": dict(evidence.dimension_values()),
                }
            ),
        )


__all__ = [
    "SCORING_POLICY_REF_KEY",
    "BehavioralEvidenceScorePolicy",
]
