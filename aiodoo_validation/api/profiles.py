"""Profile discovery metadata (Phase 11)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.enums import (
    ExecutionTier,
    OdooVersion,
    SupportedValidationProfile,
    ValidationStage,
)
from aiodoo_validation.domain.request import SUPPORTED_PROFILES
from aiodoo_validation.engine import PIPELINE_STAGE_ORDER
from aiodoo_validation.profiles.adapter_profile import AdapterProfile
from aiodoo_validation.profiles.coding.profile import CodingProfile
from aiodoo_validation.validation_plan import ProfileCapabilities


@dataclass(frozen=True, slots=True)
class ProfileInfo:
    """Static metadata describing a validation profile."""

    profile_name: str
    supported_odoo_versions: tuple[int, ...]
    supported_execution_tiers: tuple[str, ...]
    supported_runtimes: tuple[str, ...]
    supported_artifact_types: tuple[str, ...]
    capabilities: ProfileCapabilities
    pipeline_stages: tuple[ValidationStage, ...]


def list_profiles() -> tuple[str, ...]:
    """Return supported validation profile names."""
    return tuple(sorted(SUPPORTED_PROFILES))


def get_profile_info(profile_name: str) -> ProfileInfo:
    """Return static metadata for a supported profile."""
    if profile_name not in SUPPORTED_PROFILES:
        raise ValueError(f"Unsupported profile {profile_name!r}.")
    odoo_versions = (OdooVersion.V17, OdooVersion.V18, OdooVersion.V19)
    if profile_name == SupportedValidationProfile.CODING.value:
        profile = CodingProfile.create(odoo_versions=odoo_versions)
    else:
        profile = AdapterProfile.create(profile_name, odoo_versions=odoo_versions)
    return ProfileInfo(
        profile_name=profile.profile_name,
        supported_odoo_versions=odoo_versions,
        supported_execution_tiers=tuple(tier.value for tier in ExecutionTier),
        supported_runtimes=tuple(sorted(profile.supported_runtimes)),
        supported_artifact_types=tuple(sorted(profile.supported_artifact_types)),
        capabilities=profile.capabilities,
        pipeline_stages=PIPELINE_STAGE_ORDER,
    )


def capability_labels(capabilities: ProfileCapabilities) -> tuple[str, ...]:
    """Convert profile capabilities to stable string labels."""
    labels: list[str] = []
    if capabilities.supports_inference:
        labels.append("supports_inference")
    if capabilities.supports_oracles:
        labels.append("supports_oracles")
    if capabilities.supports_scoring:
        labels.append("supports_scoring")
    if capabilities.supports_benchmark:
        labels.append("supports_benchmark")
    if capabilities.supports_certification:
        labels.append("supports_certification")
    if capabilities.supports_reports:
        labels.append("supports_reports")
    return tuple(labels)
