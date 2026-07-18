"""Placeholder scoring policies (Phase 6 — no real scoring formulas)."""

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
from aiodoo_validation.oracles.ids import (
    CODING_ORACLE_BEHAVIOR,
    CODING_ORACLE_MANIFEST,
    CODING_ORACLE_METADATA,
    CODING_ORACLE_MODULE_STRUCTURE,
    CODING_ORACLE_PYTHON,
    CODING_ORACLE_QUALITY,
    CODING_ORACLE_SECURITY,
    CODING_ORACLE_XML,
)
from aiodoo_validation.scoring.ids import (
    CODING_SCORE_BEHAVIOR,
    CODING_SCORE_MANIFEST,
    CODING_SCORE_METADATA,
    CODING_SCORE_MODULE_STRUCTURE,
    CODING_SCORE_PYTHON,
    CODING_SCORE_QUALITY,
    CODING_SCORE_SECURITY,
    CODING_SCORE_XML,
    PLACEHOLDER_SCORE_VALUE,
)


def placeholder_score_metadata(
    *,
    policy_id: str,
    name: str,
    description: str,
    source_oracle_id: str,
    supported_profile: str = "coding",
    version: str = "0.0.0-placeholder",
) -> ScoreMetadata:
    return ScoreMetadata(
        policy_id=policy_id,
        name=name,
        description=description,
        version=version,
        supported_profile=supported_profile,
        source_oracle_id=source_oracle_id,
        capabilities=ScoreCapability(
            placeholder=True,
            consumes_oracle_result=True,
            inspects_filesystem=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class PlaceholderScorePolicy:
    """Base placeholder policy returning a deterministic score from OracleResult only."""

    metadata: ScoreMetadata

    def score(self, context: ScoreContext) -> ScoreResult:
        started = perf_counter()
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return ScoreResult(
            policy_id=self.metadata.policy_id,
            source_oracle_id=self.metadata.source_oracle_id,
            success=True,
            score=PLACEHOLDER_SCORE_VALUE,
            message=(
                f"Placeholder score policy {self.metadata.policy_id!r} "
                f"scored oracle {context.oracle_result.oracle_id!r}."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": True,
                    "oracle_success": context.oracle_result.success,
                    "plan_digest": context.plan_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class MetadataScorePolicy(PlaceholderScorePolicy):
    @staticmethod
    def create() -> MetadataScorePolicy:
        return MetadataScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_METADATA,
                name="Metadata Score Policy",
                description="Placeholder metadata scoring policy.",
                source_oracle_id=CODING_ORACLE_METADATA,
            )
        )


@dataclass(frozen=True, slots=True)
class ManifestScorePolicy(PlaceholderScorePolicy):
    @staticmethod
    def create() -> ManifestScorePolicy:
        return ManifestScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_MANIFEST,
                name="Manifest Score Policy",
                description="Placeholder manifest scoring policy.",
                source_oracle_id=CODING_ORACLE_MANIFEST,
            )
        )


@dataclass(frozen=True, slots=True)
class PythonScorePolicy(PlaceholderScorePolicy):
    @staticmethod
    def create() -> PythonScorePolicy:
        return PythonScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_PYTHON,
                name="Python Score Policy",
                description="Placeholder Python scoring policy.",
                source_oracle_id=CODING_ORACLE_PYTHON,
            )
        )


@dataclass(frozen=True, slots=True)
class XmlScorePolicy(PlaceholderScorePolicy):
    @staticmethod
    def create() -> XmlScorePolicy:
        return XmlScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_XML,
                name="XML Score Policy",
                description="Placeholder XML scoring policy.",
                source_oracle_id=CODING_ORACLE_XML,
            )
        )


@dataclass(frozen=True, slots=True)
class SecurityScorePolicy(PlaceholderScorePolicy):
    @staticmethod
    def create() -> SecurityScorePolicy:
        return SecurityScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_SECURITY,
                name="Security Score Policy",
                description="Placeholder security scoring policy.",
                source_oracle_id=CODING_ORACLE_SECURITY,
            )
        )


@dataclass(frozen=True, slots=True)
class ModuleStructureScorePolicy(PlaceholderScorePolicy):
    @staticmethod
    def create() -> ModuleStructureScorePolicy:
        return ModuleStructureScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_MODULE_STRUCTURE,
                name="Module Structure Score Policy",
                description="Placeholder module structure scoring policy.",
                source_oracle_id=CODING_ORACLE_MODULE_STRUCTURE,
            )
        )


@dataclass(frozen=True, slots=True)
class QualityScorePolicy(PlaceholderScorePolicy):
    """Future quality scoring policy (available for plugins; disabled in plan)."""

    @staticmethod
    def create() -> QualityScorePolicy:
        return QualityScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_QUALITY,
                name="Quality Score Policy",
                description="Placeholder future quality scoring policy.",
                source_oracle_id=CODING_ORACLE_QUALITY,
            )
        )


@dataclass(frozen=True, slots=True)
class BehaviorScorePolicy(PlaceholderScorePolicy):
    """Placeholder coding behavior scoring policy (stub path)."""

    @staticmethod
    def create() -> BehaviorScorePolicy:
        return BehaviorScorePolicy(
            metadata=placeholder_score_metadata(
                policy_id=CODING_SCORE_BEHAVIOR,
                name="Coding Behavior Score Policy",
                description="Placeholder coding behavior scoring policy.",
                source_oracle_id=CODING_ORACLE_BEHAVIOR,
            )
        )


def default_coding_placeholder_policies() -> tuple[PlaceholderScorePolicy, ...]:
    return (
        MetadataScorePolicy.create(),
        ManifestScorePolicy.create(),
        PythonScorePolicy.create(),
        XmlScorePolicy.create(),
        SecurityScorePolicy.create(),
        ModuleStructureScorePolicy.create(),
        BehaviorScorePolicy.create(),
    )
