"""Resolve profile names to profile implementations."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ProfileErrorCode, SupportedValidationProfile
from aiodoo_validation.domain.profile import ProfileError, ResolvedProfile
from aiodoo_validation.profiles.coding.policy import REJECTED_PROFILE_NAMES
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
        if normalized in REJECTED_PROFILE_NAMES:
            return None, ProfileError(
                code=ProfileErrorCode.UNSUPPORTED_PROFILE,
                message=f"Profile {profile_name!r} is not supported.",
                field="profile_name",
            )
        if normalized == SupportedValidationProfile.CODING.value:
            return CodingProfile.create(odoo_versions=context.request.odoo_versions), None
        return None, ProfileError(
            code=ProfileErrorCode.UNSUPPORTED_PROFILE,
            message=f"Unsupported profile {profile_name!r}.",
            field="profile_name",
        )
