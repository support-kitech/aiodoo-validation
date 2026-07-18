"""Production scoring policies — derive scores from real oracle outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.scoring import (
    ScoreCapability,
    ScoreContext,
    ScoreMetadata,
    ScoreResult,
)


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
    """Score 100 when the source oracle succeeded, else 0."""

    metadata: ScoreMetadata

    def score(self, context: ScoreContext) -> ScoreResult:
        started = perf_counter()
        success = bool(context.oracle_result.success)
        score = 100.0 if success else 0.0
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return ScoreResult(
            policy_id=self.metadata.policy_id,
            source_oracle_id=self.metadata.source_oracle_id,
            success=True,
            score=score,
            message=(
                f"Score {score:.1f} from oracle "
                f"{context.oracle_result.oracle_id!r} "
                f"(success={success})."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "oracle_success": success,
                    "oracle_duration_ms": context.oracle_result.duration_ms,
                }
            ),
        )


def default_production_score_policies(
    *,
    profile: str = "coding",
) -> tuple[OracleOutcomeScorePolicy, ...]:
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    return tuple(
        OracleOutcomeScorePolicy(
            metadata=_metadata(
                policy_id=f"{profile}.score.{name}",
                name=f"{name.replace('_', ' ').title()} Score",
                source_oracle_id=f"{profile}.oracle.{name}",
                supported_profile=profile,
            )
        )
        for name in names
    )


def default_production_coding_score_policies(
    *,
    supported_profile: str = "coding",
) -> tuple[OracleOutcomeScorePolicy, ...]:
    return default_production_score_policies(profile=supported_profile)


__all__ = [
    "OracleOutcomeScorePolicy",
    "default_production_coding_score_policies",
    "default_production_score_policies",
]
