"""Coding validation profile (Phase 4)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.profile import ResolvedProfile
from aiodoo_validation.profiles.coding.policy import (
    PROFILE_NAME,
    SUPPORTED_ADAPTER_TYPES,
    SUPPORTED_ARTIFACT_TYPES,
    SUPPORTED_MODEL_FAMILIES,
    SUPPORTED_PROTOCOL_MAJORS,
    SUPPORTED_RUNTIMES,
)
from aiodoo_validation.validation_plan import PipelineStagePlaceholder, ProfileCapabilities


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
            supports_oracles=False,
            supports_scoring=False,
            supports_benchmark=False,
            supports_certification=False,
        )
    )
    validation_strategy: str = "coding-v1-metadata-only"
    oracle_pipeline: tuple[PipelineStagePlaceholder, ...] = (
        PipelineStagePlaceholder(
            stage_id="coding.oracle.placeholder",
            name="Oracle pipeline placeholder",
            enabled=False,
            phase="oracle",
        ),
    )
    scoring_pipeline: tuple[PipelineStagePlaceholder, ...] = (
        PipelineStagePlaceholder(
            stage_id="coding.scoring.placeholder",
            name="Scoring pipeline placeholder",
            enabled=False,
            phase="scoring",
        ),
    )
    benchmark_pipeline: tuple[PipelineStagePlaceholder, ...] = (
        PipelineStagePlaceholder(
            stage_id="coding.benchmark.placeholder",
            name="Benchmark pipeline placeholder",
            enabled=False,
            phase="benchmark",
        ),
    )
    certification_pipeline: tuple[PipelineStagePlaceholder, ...] = (
        PipelineStagePlaceholder(
            stage_id="coding.certification.placeholder",
            name="Certification pipeline placeholder",
            enabled=False,
            phase="certification",
        ),
    )
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @staticmethod
    def create(*, odoo_versions: tuple[int, ...]) -> CodingProfile:
        return CodingProfile(
            profile_name=PROFILE_NAME,
            metadata=MappingProxyType({"odoo_versions": odoo_versions}),
        )
