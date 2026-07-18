"""Resolve profile names to profile implementations."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ProfileErrorCode, SupportedValidationProfile
from aiodoo_validation.domain.profile import ProfileError, ResolvedProfile
from aiodoo_validation.profiles.adapter_profile import ALL_ADAPTER_PROFILES, AdapterProfile
from aiodoo_validation.profiles.coding.profile import CodingProfile


@dataclass(frozen=True, slots=True)
class ProfileResolver:
    """Map requested profile names to immutable profile objects."""

    def resolve(
        self,
        profile_name: str,
        *,
        context: RunContext,
    ) -> tuple[ResolvedProfile | None, ProfileError | None]:
        normalized = profile_name.strip().lower()
        if normalized not in ALL_ADAPTER_PROFILES:
            return None, ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_PROFILE,
                message=f"Unsupported profile {profile_name!r}.",
                field="profile_name",
            )
        odoo_versions = context.request.odoo_versions
        if normalized == SupportedValidationProfile.CODING.value:
            return CodingProfile.create(odoo_versions=odoo_versions), None
        return AdapterProfile.create(normalized, odoo_versions=odoo_versions), None
