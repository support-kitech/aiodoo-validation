"""Validation plan domain types (Phase 4)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.enums import ValidationStage


@dataclass(frozen=True, slots=True)
class ProfileCapabilities:
    """Declared capabilities for a validation profile."""

    supports_inference: bool = True
    supports_oracles: bool = False
    supports_scoring: bool = False
    supports_benchmark: bool = False
    supports_certification: bool = False


@dataclass(frozen=True, slots=True)
class PipelineStagePlaceholder:
    """Placeholder metadata for a future pipeline stage."""

    stage_id: str
    name: str
    enabled: bool
    phase: str


@dataclass(frozen=True, slots=True)
class ValidationPlan:
    """
    Immutable validation plan metadata.

    Describes what a profile will execute in later phases without running validation.
    """

    profile_name: str
    plan_digest: str
    capabilities: ProfileCapabilities
    supported_artifact_types: tuple[str, ...]
    supported_runtimes: tuple[str, ...]
    oracle_pipeline: tuple[PipelineStagePlaceholder, ...]
    scoring_pipeline: tuple[PipelineStagePlaceholder, ...]
    benchmark_pipeline: tuple[PipelineStagePlaceholder, ...]
    certification_pipeline: tuple[PipelineStagePlaceholder, ...]
    execution_order: tuple[ValidationStage, ...]
    validation_stages: tuple[ValidationStage, ...]
    configuration: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
