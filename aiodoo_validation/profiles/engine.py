"""Profile engine implementation (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ProfileErrorCode
from aiodoo_validation.domain.profile import ProfileError, ProfileResolutionOutcome, ResolvedProfile
from aiodoo_validation.profiles.coding.profile import CodingProfile
from aiodoo_validation.profiles.resolver import ProfileResolver
from aiodoo_validation.validation_plan.plan import ValidationPlan


@dataclass(frozen=True, slots=True)
class ProfileEngine:
    """
    Resolve validation profiles and construct ValidationPlan metadata.

    Phase 4 refinement: coding-specific compatibility and plan construction
    live on ``CodingProfile`` methods. ``ProfileEngine`` retains a single
    ``isinstance(CodingProfile)`` dispatch because only the coding profile
    exists today. A profile-operation Protocol would add indirection without
    benefit until a second profile is introduced.
    """

    resolver: ProfileResolver

    @classmethod
    def create_default(cls) -> ProfileEngine:
        return cls(resolver=ProfileResolver())

    def resolve_profile(self, context: RunContext) -> ProfileResolutionOutcome:
        try:
            return self._resolve_profile(context)
        except ProfileError as exc:
            return ProfileResolutionOutcome(
                success=False,
                message="Profile resolution failed.",
                errors=(exc,),
            )
        except Exception as exc:  # noqa: BLE001 — profile engine must never crash callers
            return ProfileResolutionOutcome(
                success=False,
                message="Profile resolution failed.",
                errors=(
                    ProfileError(
                        code=ProfileErrorCode.PROFILE_CONSTRUCTION_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _resolve_profile(self, context: RunContext) -> ProfileResolutionOutcome:
        bundle = context.artifact_bundle
        if bundle is None:
            return ProfileResolutionOutcome(
                success=False,
                message="Profile resolution failed.",
                errors=(
                    ProfileError(
                        code=ProfileErrorCode.MISSING_BUNDLE,
                        message="Artifact bundle is required before profile resolution.",
                        field="artifact_bundle",
                    ),
                ),
            )

        profile_name = context.request.profile_name
        profile, resolve_error = self.resolver.resolve(profile_name, context=context)
        if resolve_error is not None or profile is None:
            return ProfileResolutionOutcome(
                success=False,
                message="Profile resolution failed.",
                errors=(
                    resolve_error
                    or ProfileError(
                        code=ProfileErrorCode.PROFILE_CONSTRUCTION_FAILURE,
                        message="Profile could not be constructed.",
                    ),
                ),
            )

        compatibility_errors = self._validate_compatibility(profile, bundle)
        if compatibility_errors:
            return ProfileResolutionOutcome(
                success=False,
                message="Profile resolution failed.",
                errors=compatibility_errors,
            )

        plan = self._build_plan(profile, bundle=bundle, context=context)
        return ProfileResolutionOutcome(
            success=True,
            message="Profile resolved successfully.",
            profile=profile,
            plan=plan,
        )

    def _validate_compatibility(
        self,
        profile: ResolvedProfile,
        bundle: ArtifactBundle,
    ) -> tuple[ProfileError, ...]:
        if isinstance(profile, CodingProfile):
            return profile.validate_compatibility(bundle)
        return (
            ProfileError(
                code=ProfileErrorCode.PROFILE_CONSTRUCTION_FAILURE,
                message=f"Unknown profile type for {profile.profile_name!r}.",
            ),
        )

    def _build_plan(
        self,
        profile: ResolvedProfile,
        *,
        bundle: ArtifactBundle,
        context: RunContext,
    ) -> ValidationPlan:
        if isinstance(profile, CodingProfile):
            return profile.build_validation_plan(bundle=bundle, context=context)
        raise ProfileError(
            code=ProfileErrorCode.PROFILE_CONSTRUCTION_FAILURE,
            message=f"Cannot build plan for profile {profile.profile_name!r}.",
        )
