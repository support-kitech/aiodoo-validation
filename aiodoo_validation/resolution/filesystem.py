"""Filesystem artifact resolver (Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.domain.artifact_paths import (
    ARTIFACT_PATHS_KEY,
    build_artifact_paths_metadata,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import ArtifactResolutionErrorCode, ArtifactType
from aiodoo_validation.domain.resolution import ArtifactResolutionError, ArtifactResolutionOutcome
from aiodoo_validation.resolution.common import (
    build_artifact_bundle,
    effective_fingerprint_policy,
    resolve_descriptor,
)
from aiodoo_validation.resolution.compatibility import validate_no_duplicate_locations
from aiodoo_validation.resolution.fingerprint import (
    FingerprintProviderPort,
    PlaceholderFingerprintProvider,
)


@dataclass(frozen=True, slots=True)
class FilesystemArtifactResolver:
    """Resolve artifacts from local filesystem directories."""

    fingerprint_provider: FingerprintProviderPort

    @classmethod
    def create_default(cls) -> FilesystemArtifactResolver:
        return cls(fingerprint_provider=PlaceholderFingerprintProvider())

    def resolve(self, context: RunContext) -> ArtifactResolutionOutcome:
        try:
            return self._resolve(context)
        except OSError as exc:
            return ArtifactResolutionOutcome(
                success=False,
                message="Artifact resolution failed due to filesystem error.",
                errors=(
                    ArtifactResolutionError(
                        code=ArtifactResolutionErrorCode.RESOLVER_FAILURE,
                        message=str(exc),
                    ),
                ),
            )
        except Exception as exc:  # noqa: BLE001 — resolver must never crash callers
            return ArtifactResolutionOutcome(
                success=False,
                message="Artifact resolution failed due to internal error.",
                errors=(
                    ArtifactResolutionError(
                        code=ArtifactResolutionErrorCode.RESOLVER_FAILURE,
                        message=str(exc),
                    ),
                ),
            )

    def _resolve(self, context: RunContext) -> ArtifactResolutionOutcome:
        request = context.request
        policy = effective_fingerprint_policy(request)
        errors: list[ArtifactResolutionError] = []
        warnings: list[str] = []

        base_model, base_errors, base_warnings = resolve_descriptor(
            logical_ref="base_model",
            path_ref=request.base_model_ref,
            expected_type=ArtifactType.BASE_MODEL,
            request=request,
            fingerprint_provider=self.fingerprint_provider,
            fingerprint_policy=policy,
        )
        errors.extend(base_errors)
        warnings.extend(base_warnings)

        adapter, adapter_errors, adapter_warnings = resolve_descriptor(
            logical_ref="adapter",
            path_ref=request.adapter_ref,
            expected_type=ArtifactType.CODING_ADAPTER,
            request=request,
            fingerprint_provider=self.fingerprint_provider,
            fingerprint_policy=policy,
        )
        errors.extend(adapter_errors)
        warnings.extend(adapter_warnings)

        merged_model = None
        if request.merged_model_ref:
            merged_model, merged_errors, merged_warnings = resolve_descriptor(
                logical_ref="merged_model",
                path_ref=request.merged_model_ref,
                expected_type=ArtifactType.MERGED_MODEL,
                request=request,
                fingerprint_provider=self.fingerprint_provider,
                fingerprint_policy=policy,
            )
            errors.extend(merged_errors)
            warnings.extend(merged_warnings)

        if base_model is None or adapter is None:
            return ArtifactResolutionOutcome(
                success=False,
                message="Artifact resolution failed.",
                errors=tuple(errors),
                warnings=tuple(warnings),
            )

        if request.merged_model_ref and merged_model is None:
            return ArtifactResolutionOutcome(
                success=False,
                message="Artifact resolution failed.",
                errors=tuple(errors),
                warnings=tuple(warnings),
            )

        descriptors = (base_model, adapter) if merged_model is None else (
            base_model,
            adapter,
            merged_model,
        )
        errors.extend(validate_no_duplicate_locations(descriptors))

        if errors:
            return ArtifactResolutionOutcome(
                success=False,
                message="Artifact resolution failed.",
                errors=tuple(errors),
                warnings=tuple(warnings),
            )

        bundle = build_artifact_bundle(
            request,
            base_model=base_model,
            adapter=adapter,
            merged_model=merged_model,
            fingerprint_policy=policy,
            metadata={
                "resolver": "filesystem",
                **{ARTIFACT_PATHS_KEY: build_artifact_paths_metadata(
                    base_model=request.base_model_ref,
                    adapter=request.adapter_ref,
                    merged_model=request.merged_model_ref,
                )},
            },
        )
        return ArtifactResolutionOutcome(
            success=True,
            message="Artifacts resolved successfully.",
            bundle=bundle,
            warnings=tuple(warnings),
        )
