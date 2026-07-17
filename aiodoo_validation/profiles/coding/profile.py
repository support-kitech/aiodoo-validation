"""Coding validation profile (Phase 4+)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.benchmark.ids import (
    CODING_BENCHMARK_MANIFEST,
    CODING_BENCHMARK_METADATA,
    CODING_BENCHMARK_MODULE_STRUCTURE,
    CODING_BENCHMARK_PYTHON,
    CODING_BENCHMARK_QUALITY,
    CODING_BENCHMARK_SECURITY,
    CODING_BENCHMARK_XML,
)
from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_MANIFEST,
    CODING_CERTIFICATION_METADATA,
    CODING_CERTIFICATION_MODULE_STRUCTURE,
    CODING_CERTIFICATION_PYTHON,
    CODING_CERTIFICATION_QUALITY,
    CODING_CERTIFICATION_SECURITY,
    CODING_CERTIFICATION_XML,
)
from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.profile import ProfileError, ResolvedProfile
from aiodoo_validation.oracles.ids import (
    CODING_ORACLE_MANIFEST,
    CODING_ORACLE_METADATA,
    CODING_ORACLE_MODULE_STRUCTURE,
    CODING_ORACLE_PYTHON,
    CODING_ORACLE_QUALITY,
    CODING_ORACLE_SECURITY,
    CODING_ORACLE_XML,
)
from aiodoo_validation.profiles.coding.compatibility import validate_coding_artifact_compatibility
from aiodoo_validation.profiles.coding.policy import (
    PROFILE_NAME,
    SUPPORTED_ADAPTER_TYPES,
    SUPPORTED_ARTIFACT_TYPES,
    SUPPORTED_MODEL_FAMILIES,
    SUPPORTED_PROTOCOL_MAJORS,
    SUPPORTED_RUNTIMES,
)
from aiodoo_validation.scoring.ids import (
    CODING_SCORE_MANIFEST,
    CODING_SCORE_METADATA,
    CODING_SCORE_MODULE_STRUCTURE,
    CODING_SCORE_PYTHON,
    CODING_SCORE_QUALITY,
    CODING_SCORE_SECURITY,
    CODING_SCORE_XML,
)
from aiodoo_validation.validation_plan import (
    PipelineStagePlaceholder,
    ProfileCapabilities,
    ValidationPlan,
)

CODING_ORACLE_PIPELINE: tuple[PipelineStagePlaceholder, ...] = (
    PipelineStagePlaceholder(
        stage_id=CODING_ORACLE_METADATA,
        name="Metadata Oracle",
        enabled=True,
        phase="oracle",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_ORACLE_MANIFEST,
        name="Manifest Oracle",
        enabled=True,
        phase="oracle",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_ORACLE_PYTHON,
        name="Python Oracle",
        enabled=True,
        phase="oracle",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_ORACLE_XML,
        name="XML Oracle",
        enabled=True,
        phase="oracle",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_ORACLE_SECURITY,
        name="Security Oracle",
        enabled=True,
        phase="oracle",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_ORACLE_MODULE_STRUCTURE,
        name="Module Structure Oracle",
        enabled=True,
        phase="oracle",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_ORACLE_QUALITY,
        name="Future Quality Oracle",
        enabled=False,
        phase="oracle",
    ),
)

CODING_SCORING_PIPELINE: tuple[PipelineStagePlaceholder, ...] = (
    PipelineStagePlaceholder(
        stage_id=CODING_SCORE_METADATA,
        name="Metadata Score Policy",
        enabled=True,
        phase="scoring",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_SCORE_MANIFEST,
        name="Manifest Score Policy",
        enabled=True,
        phase="scoring",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_SCORE_PYTHON,
        name="Python Score Policy",
        enabled=True,
        phase="scoring",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_SCORE_XML,
        name="XML Score Policy",
        enabled=True,
        phase="scoring",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_SCORE_SECURITY,
        name="Security Score Policy",
        enabled=True,
        phase="scoring",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_SCORE_MODULE_STRUCTURE,
        name="Module Structure Score Policy",
        enabled=True,
        phase="scoring",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_SCORE_QUALITY,
        name="Future Quality Score Policy",
        enabled=False,
        phase="scoring",
    ),
)

CODING_BENCHMARK_PIPELINE: tuple[PipelineStagePlaceholder, ...] = (
    PipelineStagePlaceholder(
        stage_id=CODING_BENCHMARK_METADATA,
        name="Metadata Benchmark Policy",
        enabled=True,
        phase="benchmark",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_BENCHMARK_MANIFEST,
        name="Manifest Benchmark Policy",
        enabled=True,
        phase="benchmark",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_BENCHMARK_PYTHON,
        name="Python Benchmark Policy",
        enabled=True,
        phase="benchmark",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_BENCHMARK_XML,
        name="XML Benchmark Policy",
        enabled=True,
        phase="benchmark",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_BENCHMARK_SECURITY,
        name="Security Benchmark Policy",
        enabled=True,
        phase="benchmark",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_BENCHMARK_MODULE_STRUCTURE,
        name="Module Structure Benchmark Policy",
        enabled=True,
        phase="benchmark",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_BENCHMARK_QUALITY,
        name="Future Quality Benchmark Policy",
        enabled=False,
        phase="benchmark",
    ),
)

CODING_CERTIFICATION_PIPELINE: tuple[PipelineStagePlaceholder, ...] = (
    PipelineStagePlaceholder(
        stage_id=CODING_CERTIFICATION_METADATA,
        name="Metadata Certification Policy",
        enabled=True,
        phase="certification",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_CERTIFICATION_MANIFEST,
        name="Manifest Certification Policy",
        enabled=True,
        phase="certification",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_CERTIFICATION_PYTHON,
        name="Python Certification Policy",
        enabled=True,
        phase="certification",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_CERTIFICATION_XML,
        name="XML Certification Policy",
        enabled=True,
        phase="certification",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_CERTIFICATION_SECURITY,
        name="Security Certification Policy",
        enabled=True,
        phase="certification",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_CERTIFICATION_MODULE_STRUCTURE,
        name="Module Structure Certification Policy",
        enabled=True,
        phase="certification",
    ),
    PipelineStagePlaceholder(
        stage_id=CODING_CERTIFICATION_QUALITY,
        name="Future Quality Certification Policy",
        enabled=False,
        phase="certification",
    ),
)


@dataclass(frozen=True, slots=True)
class CodingProfile(ResolvedProfile):
    """Immutable coding validation profile metadata."""

    supported_model_families: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(SUPPORTED_MODEL_FAMILIES))
    )
    supported_adapter_types: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(SUPPORTED_ADAPTER_TYPES))
    )
    supported_artifact_types: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(SUPPORTED_ARTIFACT_TYPES))
    )
    supported_protocol_majors: tuple[int, ...] = field(
        default_factory=lambda: tuple(sorted(SUPPORTED_PROTOCOL_MAJORS))
    )
    supported_runtimes: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(SUPPORTED_RUNTIMES))
    )
    capabilities: ProfileCapabilities = field(
        default_factory=lambda: ProfileCapabilities(
            supports_inference=True,
            supports_oracles=True,
            supports_scoring=True,
            supports_benchmark=True,
            supports_certification=True,
        )
    )
    validation_strategy: str = "coding-v1-certification-placeholders"
    oracle_pipeline: tuple[PipelineStagePlaceholder, ...] = CODING_ORACLE_PIPELINE
    scoring_pipeline: tuple[PipelineStagePlaceholder, ...] = CODING_SCORING_PIPELINE
    benchmark_pipeline: tuple[PipelineStagePlaceholder, ...] = CODING_BENCHMARK_PIPELINE
    certification_pipeline: tuple[PipelineStagePlaceholder, ...] = CODING_CERTIFICATION_PIPELINE
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @staticmethod
    def create(*, odoo_versions: tuple[int, ...]) -> CodingProfile:
        return CodingProfile(
            profile_name=PROFILE_NAME,
            metadata=MappingProxyType({"odoo_versions": odoo_versions}),
        )

    def validate_compatibility(self, bundle: ArtifactBundle) -> tuple[ProfileError, ...]:
        """Validate resolved artifacts against coding profile policy."""
        return validate_coding_artifact_compatibility(bundle)

    def build_validation_plan(
        self,
        *,
        bundle: ArtifactBundle,
        context: RunContext,
    ) -> ValidationPlan:
        """Construct an immutable ValidationPlan for this profile."""
        from aiodoo_validation.profiles.coding.plan_builder import build_coding_validation_plan

        return build_coding_validation_plan(self, bundle=bundle, context=context)
