"""Shared adapter validation profile factory for all PEFT adapter products."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.corpus.governance import resolve_evaluation_corpus_configuration
from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ArtifactType,
    ProfileErrorCode,
    SupportedValidationProfile,
    ValidationStage,
)
from aiodoo_validation.domain.profile import ProfileError, ResolvedProfile
from aiodoo_validation.validation_plan import (
    PipelineStagePlaceholder,
    ProfileCapabilities,
    ValidationPlan,
)

_STAGE_NAMES = (
    "metadata",
    "manifest",
    "python",
    "xml",
    "security",
    "module_structure",
)


def _pipeline(profile: str, phase: str) -> tuple[PipelineStagePlaceholder, ...]:
    stages = [
        PipelineStagePlaceholder(
            stage_id=f"{profile}.{phase}.{name}",
            name=f"{name.replace('_', ' ').title()}",
            enabled=True,
            phase=phase,
        )
        for name in _STAGE_NAMES
    ]
    stages.append(
        PipelineStagePlaceholder(
            stage_id=f"{profile}.{phase}.quality",
            name="Quality",
            enabled=False,
            phase=phase,
        )
    )
    return tuple(stages)


_BEHAVIOR_PROFILES = frozenset(
    {
        SupportedValidationProfile.REPAIR.value,
        SupportedValidationProfile.PLANNER.value,
        SupportedValidationProfile.CONVERSATION.value,
        SupportedValidationProfile.EXECUTION.value,
    }
)


def _behavior_oracle_stage(profile: str) -> PipelineStagePlaceholder:
    return PipelineStagePlaceholder(
        stage_id=f"{profile}.oracle.behavior.{profile}",
        name=f"{profile.title()} Behavior",
        enabled=True,
        phase="oracle",
    )


def _oracle_pipeline_for_profile(profile: str) -> tuple[PipelineStagePlaceholder, ...]:
    """Structural oracle stages, plus capability behavioral stage when wired."""
    stages = list(_pipeline(profile, "oracle"))
    if profile in _BEHAVIOR_PROFILES:
        stages.append(_behavior_oracle_stage(profile))
    return tuple(stages)


def _scoring_pipeline_for_profile(profile: str) -> tuple[PipelineStagePlaceholder, ...]:
    """Structural score stages, plus capability behavioral score when wired."""
    stages = list(_pipeline(profile, "score"))
    if profile in _BEHAVIOR_PROFILES:
        stages.append(
            PipelineStagePlaceholder(
                stage_id=f"{profile}.score.behavior",
                name=f"{profile.title()} Behavior Score",
                enabled=True,
                phase="score",
            )
        )
    return tuple(stages)


def _benchmark_pipeline_for_profile(profile: str) -> tuple[PipelineStagePlaceholder, ...]:
    """Structural benchmarks, plus capability behavioral benchmark when wired."""
    stages = list(_pipeline(profile, "benchmark"))
    if profile in _BEHAVIOR_PROFILES:
        stages.append(
            PipelineStagePlaceholder(
                stage_id=f"{profile}.benchmark.behavior",
                name=f"{profile.title()} Behavior Benchmark",
                enabled=True,
                phase="benchmark",
            )
        )
    return tuple(stages)


def _certification_pipeline_for_profile(profile: str) -> tuple[PipelineStagePlaceholder, ...]:
    """Structural certification, plus capability behavior gate when wired."""
    stages = list(_pipeline(profile, "certification"))
    if profile in _BEHAVIOR_PROFILES:
        stages.append(
            PipelineStagePlaceholder(
                stage_id=f"{profile}.certification.behavior",
                name=f"{profile.title()} Behavior Certification",
                enabled=True,
                phase="certification",
            )
        )
    return tuple(stages)


def _report_pipeline_for_profile(profile: str) -> tuple[PipelineStagePlaceholder, ...]:
    """Structural reports, plus capability behavior certification report when wired."""
    stages = list(_pipeline(profile, "report"))
    if profile in _BEHAVIOR_PROFILES:
        stages.append(
            PipelineStagePlaceholder(
                stage_id=f"{profile}.report.behavior",
                name=f"{profile.title()} Behavior Report",
                enabled=True,
                phase="report",
            )
        )
    return tuple(stages)


def validate_adapter_profile_compatibility(
    bundle: ArtifactBundle,
    *,
    profile_name: str,
) -> tuple[ProfileError, ...]:
    """Validate base + adapter metadata against a named adapter profile."""
    errors: list[ProfileError] = []
    profile = profile_name.strip().lower()

    if bundle.base_model.artifact_type is not ArtifactType.BASE_MODEL:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_MODEL,
                message=f"{profile} profile requires a base model artifact.",
                field="base_model",
            )
        )
    if bundle.adapter.artifact_type is not ArtifactType.CODING_ADAPTER:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_ADAPTER,
                message=(
                    f"{profile} profile requires a PEFT adapter artifact "
                    "(artifact_type=coding_adapter)."
                ),
                field="adapter",
            )
        )

    adapter_type = str(bundle.adapter.metadata.get("adapter_type", "")).strip().lower()
    if adapter_type != profile:
        errors.append(
            ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_ADAPTER,
                message=f"{profile} profile requires adapter_type={profile!r}.",
                field="adapter",
            )
        )
    return tuple(errors)


@dataclass(frozen=True, slots=True)
class AdapterProfile(ResolvedProfile):
    """Production adapter profile for non-coding PEFT products."""

    odoo_versions: tuple[int, ...] = ()
    capabilities: ProfileCapabilities = field(
        default_factory=lambda: ProfileCapabilities(
            supports_inference=True,
            supports_oracles=True,
            supports_scoring=True,
            supports_benchmark=True,
            supports_certification=True,
            supports_reports=True,
        )
    )
    validation_strategy: str = "adapter-v1-structural"
    oracle_pipeline: tuple[PipelineStagePlaceholder, ...] = ()
    scoring_pipeline: tuple[PipelineStagePlaceholder, ...] = ()
    benchmark_pipeline: tuple[PipelineStagePlaceholder, ...] = ()
    certification_pipeline: tuple[PipelineStagePlaceholder, ...] = ()
    report_pipeline: tuple[PipelineStagePlaceholder, ...] = ()
    supported_artifact_types: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                ArtifactType.BASE_MODEL.value,
                ArtifactType.CODING_ADAPTER.value,
                ArtifactType.MERGED_MODEL.value,
            }
        )
    )
    supported_runtimes: frozenset[str] = field(
        default_factory=lambda: frozenset({"mock", "stub", "qwen_hf"})
    )
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @classmethod
    def create(
        cls,
        profile_name: str,
        *,
        odoo_versions: tuple[int, ...],
    ) -> AdapterProfile:
        profile = profile_name.strip().lower()
        return cls(
            profile_name=profile,
            odoo_versions=odoo_versions,
            oracle_pipeline=_oracle_pipeline_for_profile(profile),
            scoring_pipeline=_scoring_pipeline_for_profile(profile),
            benchmark_pipeline=_benchmark_pipeline_for_profile(profile),
            certification_pipeline=_certification_pipeline_for_profile(profile),
            report_pipeline=_report_pipeline_for_profile(profile),
            metadata=MappingProxyType({"odoo_versions": odoo_versions, "adapter_type": profile}),
        )

    def validate_compatibility(self, bundle: ArtifactBundle) -> tuple[ProfileError, ...]:
        return validate_adapter_profile_compatibility(bundle, profile_name=self.profile_name)

    def build_validation_plan(
        self,
        *,
        bundle: ArtifactBundle,
        context: RunContext,
    ) -> ValidationPlan:
        digest_material = "|".join(
            (
                self.profile_name,
                bundle.bundle_digest,
                context.execution_tier.value,
                str(context.protocol_major),
            )
        )
        plan_digest = hashlib.sha256(digest_material.encode("utf-8")).hexdigest()[:16]
        return ValidationPlan(
            profile_name=self.profile_name,
            plan_digest=plan_digest,
            capabilities=self.capabilities,
            supported_artifact_types=tuple(sorted(self.supported_artifact_types)),
            supported_runtimes=tuple(sorted(self.supported_runtimes)),
            oracle_pipeline=self.oracle_pipeline,
            scoring_pipeline=self.scoring_pipeline,
            benchmark_pipeline=self.benchmark_pipeline,
            certification_pipeline=self.certification_pipeline,
            report_pipeline=self.report_pipeline,
            execution_order=(
                ValidationStage.INITIALIZE_INFERENCE,
                ValidationStage.RUN_VALIDATION,
                ValidationStage.SCORING,
                ValidationStage.BENCHMARK,
                ValidationStage.CERTIFICATION,
                ValidationStage.REPORT,
            ),
            validation_stages=(ValidationStage.RUN_VALIDATION,),
            configuration={
                "execution_tier": context.execution_tier.value,
                "protocol_major": context.protocol_major,
                "protocol_minor": context.protocol_minor,
                "odoo_versions": context.request.odoo_versions,
                "bundle_digest": bundle.bundle_digest,
                **dict(
                    resolve_evaluation_corpus_configuration(
                        capability_id=self.profile_name,
                        metadata=context.request.metadata,
                    )
                ),
            },
        )


ALL_ADAPTER_PROFILES: frozenset[str] = frozenset(
    member.value for member in SupportedValidationProfile
)


__all__ = [
    "ALL_ADAPTER_PROFILES",
    "AdapterProfile",
    "validate_adapter_profile_compatibility",
]
