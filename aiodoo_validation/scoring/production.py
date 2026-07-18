"""Production scoring policies — derive scores from real oracle outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.enums import ValidationKind
from aiodoo_validation.domain.scoring import (
    ScoreCapability,
    ScoreContext,
    ScoreMetadata,
    ScoreResult,
)
from aiodoo_validation.scoring.behavioral import BehavioralEvidenceScorePolicy
from aiodoo_validation.scoring.dimensions import (
    behavior_dimensions_from_suite,
    structural_dimensions_from_oracle,
)
from aiodoo_validation.scoring.evidence import interpret_behavioral_oracle_evidence


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
        description=f"Production score from oracle {source_oracle_id}.",
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
class OracleOutcomeScorePolicy:
    """
    Score from oracle outcome.

    Structural oracles: 100 on success, 0 on failure.
    Behavioral oracles (when enabled): use suite pass_rate; deferred → 0.
    Emits multi-dimensional metadata for future weighted certification.
    """

    metadata: ScoreMetadata

    def score(self, context: ScoreContext) -> ScoreResult:
        started = perf_counter()
        oracle_meta = context.oracle_result.metadata
        success = bool(context.oracle_result.success)
        deferred = bool(oracle_meta.get("deferred", False))
        kind = str(oracle_meta.get("validation_kind", ValidationKind.STRUCTURAL.value))

        if kind == ValidationKind.BEHAVIORAL.value:
            # Prefer interpreted suite evidence (pass_rate or pass_count/case_count).
            evidence = interpret_behavioral_oracle_evidence(context.oracle_result)
            if evidence.pass_rate is not None:
                score = float(evidence.pass_rate)
                dimensions = behavior_dimensions_from_suite(
                    pass_rate=score,
                    oracle_score=score,
                )
            elif deferred:
                score = 0.0
                dimensions = behavior_dimensions_from_suite(pass_rate=None, oracle_score=0.0)
            else:
                score = 100.0 if success else 0.0
                dimensions = behavior_dimensions_from_suite(
                    pass_rate=score,
                    oracle_score=score,
                )
        else:
            score = 100.0 if success else 0.0
            dimensions = structural_dimensions_from_oracle(
                oracle_success=success,
                score=score,
            )

        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return ScoreResult(
            policy_id=self.metadata.policy_id,
            source_oracle_id=self.metadata.source_oracle_id,
            success=True,
            score=score,
            message=(
                f"Score {score:.1f} from oracle "
                f"{context.oracle_result.oracle_id!r} "
                f"(success={success}, kind={kind})."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "oracle_success": success,
                    "oracle_duration_ms": context.oracle_result.duration_ms,
                    "deferred": deferred,
                    "dimensions": dict(dimensions.as_mapping()),
                    "tokens_per_sec": oracle_meta.get("tokens_per_sec"),
                    "memory_mb": oracle_meta.get("memory_mb"),
                    "latency_ms": oracle_meta.get("latency_ms"),
                }
            ),
        )


def default_production_score_policies(
    *,
    profile: str = "coding",
) -> tuple[OracleOutcomeScorePolicy | BehavioralEvidenceScorePolicy, ...]:
    """
    Structural outcome policies for every adapter profile.

    Profiles with Capability Delivery behavior packs additionally register the
    E6 behavioral evidence policy when ``profile`` matches.
    """
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    policies: list[OracleOutcomeScorePolicy | BehavioralEvidenceScorePolicy] = [
        OracleOutcomeScorePolicy(
            metadata=_metadata(
                policy_id=f"{profile}.score.{name}",
                name=f"{name.replace('_', ' ').title()} Score",
                source_oracle_id=f"{profile}.oracle.{name}",
                supported_profile=profile,
            )
        )
        for name in names
    ]
    if profile == "approval":
        policies.append(BehavioralEvidenceScorePolicy.create_for_approval())
    if profile == "coding":
        policies.append(BehavioralEvidenceScorePolicy.create_for_coding())
    if profile == "conversation":
        policies.append(BehavioralEvidenceScorePolicy.create_for_conversation())
    if profile == "evaluation":
        policies.append(BehavioralEvidenceScorePolicy.create_for_evaluation())
    if profile == "execution":
        policies.append(BehavioralEvidenceScorePolicy.create_for_execution())
    if profile == "planner":
        policies.append(BehavioralEvidenceScorePolicy.create_for_planner())
    if profile == "repair":
        policies.append(BehavioralEvidenceScorePolicy.create_for_repair())
    return tuple(policies)


def default_production_coding_score_policies(
    *,
    supported_profile: str = "coding",
) -> tuple[OracleOutcomeScorePolicy | BehavioralEvidenceScorePolicy, ...]:
    return default_production_score_policies(profile=supported_profile)


__all__ = [
    "BehavioralEvidenceScorePolicy",
    "OracleOutcomeScorePolicy",
    "default_production_coding_score_policies",
    "default_production_score_policies",
]
