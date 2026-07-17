"""Shared artifact resolution helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.artifacts import ArtifactBundle, ArtifactDescriptor
from aiodoo_validation.domain.enums import (
    ArtifactResolutionErrorCode,
    ArtifactType,
    FingerprintPolicy,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.resolution import ArtifactResolutionError
from aiodoo_validation.resolution.fingerprint import FingerprintProviderPort

ARTIFACT_METADATA_FILENAME = "artifact.json"
SUPPORTED_ARTIFACT_TYPES = frozenset({member.value for member in ArtifactType})
REJECTED_ADAPTER_TYPES = frozenset({"planner", "repair", "conversation", "execution", "evaluation"})


def effective_fingerprint_policy(request: ValidationRequest) -> FingerprintPolicy:
    if request.strict_fingerprint_policy:
        return FingerprintPolicy.STRICT
    return request.fingerprint_policy


def build_bundle_digest(*digests: str) -> str:
    material = "|".join(digests).encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:16]


def build_artifact_bundle(
    request: ValidationRequest,
    *,
    base_model: ArtifactDescriptor,
    adapter: ArtifactDescriptor,
    merged_model: ArtifactDescriptor | None,
    fingerprint_policy: FingerprintPolicy,
    metadata: Mapping[str, Any] | None = None,
) -> ArtifactBundle:
    digests = [base_model.location_digest, adapter.location_digest]
    if merged_model is not None:
        digests.append(merged_model.location_digest)
    return ArtifactBundle(
        base_model=base_model,
        adapter=adapter,
        merged_model=merged_model,
        protocol_major=request.protocol_major,
        protocol_minor=request.protocol_minor,
        fingerprint_policy=fingerprint_policy,
        bundle_digest=build_bundle_digest(*digests),
        metadata=MappingProxyType(dict(metadata or {})),
    )


def read_artifact_metadata(
    path: Path,
) -> tuple[Mapping[str, Any] | None, ArtifactResolutionError | None]:
    metadata_path = path / ARTIFACT_METADATA_FILENAME
    if not metadata_path.is_file():
        return None, ArtifactResolutionError(
            code=ArtifactResolutionErrorCode.MISSING_METADATA,
            message=f"Missing {ARTIFACT_METADATA_FILENAME} in {path}.",
            field=str(path),
        )
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, ArtifactResolutionError(
            code=ArtifactResolutionErrorCode.MISSING_METADATA,
            message=f"Invalid {ARTIFACT_METADATA_FILENAME}: {exc}",
            field=str(path),
        )
    if not isinstance(payload, dict):
        return None, ArtifactResolutionError(
            code=ArtifactResolutionErrorCode.MISSING_METADATA,
            message=f"{ARTIFACT_METADATA_FILENAME} must be a JSON object.",
            field=str(path),
        )
    return MappingProxyType(payload), None


def validate_artifact_metadata(
    metadata: Mapping[str, Any],
    *,
    logical_ref: str,
    request: ValidationRequest,
) -> tuple[ArtifactType | None, tuple[ArtifactResolutionError, ...], tuple[str, ...]]:
    errors: list[ArtifactResolutionError] = []
    warnings: list[str] = []

    raw_type = metadata.get("artifact_type")
    if not isinstance(raw_type, str) or not raw_type.strip():
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.MISSING_METADATA,
                message="artifact_type is required in artifact metadata.",
                field=logical_ref,
            )
        )
        return None, tuple(errors), tuple(warnings)

    artifact_type_value = raw_type.strip().lower()
    if artifact_type_value not in SUPPORTED_ARTIFACT_TYPES:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.UNSUPPORTED_ARTIFACT,
                message=f"Unsupported artifact_type {artifact_type_value!r}.",
                field=logical_ref,
            )
        )
        return None, tuple(errors), tuple(warnings)

    artifact_type = ArtifactType(artifact_type_value)

    adapter_type = metadata.get("adapter_type")
    if isinstance(adapter_type, str):
        normalized_adapter_type = adapter_type.strip().lower()
        if normalized_adapter_type in REJECTED_ADAPTER_TYPES:
            errors.append(
                ArtifactResolutionError(
                    code=ArtifactResolutionErrorCode.UNSUPPORTED_ARTIFACT,
                    message=f"Adapter type {normalized_adapter_type!r} is not supported.",
                    field=logical_ref,
                )
            )

    protocol_major = metadata.get("protocol_major")
    if protocol_major is None:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.MISSING_METADATA,
                message="protocol_major is required in artifact metadata.",
                field=logical_ref,
            )
        )
    elif not isinstance(protocol_major, int):
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.INVALID_PROTOCOL,
                message="protocol_major must be an integer.",
                field=logical_ref,
            )
        )
    elif protocol_major != request.protocol_major:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.INVALID_PROTOCOL,
                message=(
                    f"Artifact protocol_major {protocol_major} does not match "
                    f"request protocol_major {request.protocol_major}."
                ),
                field=logical_ref,
            )
        )

    return artifact_type, tuple(errors), tuple(warnings)


def resolve_descriptor(
    *,
    logical_ref: str,
    path_ref: str,
    expected_type: ArtifactType | None,
    request: ValidationRequest,
    fingerprint_provider: FingerprintProviderPort,
    fingerprint_policy: FingerprintPolicy,
) -> tuple[ArtifactDescriptor | None, tuple[ArtifactResolutionError, ...], tuple[str, ...]]:
    errors: list[ArtifactResolutionError] = []
    warnings: list[str] = []

    if not path_ref.strip():
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.MISSING_PATH,
                message=f"Missing path for {logical_ref!r}.",
                field=logical_ref,
            )
        )
        return None, tuple(errors), tuple(warnings)

    path = Path(path_ref)
    if not path.exists():
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.MISSING_PATH,
                message=f"Path does not exist for {logical_ref!r}: {path_ref}",
                field=logical_ref,
            )
        )
        return None, tuple(errors), tuple(warnings)

    if not path.is_dir():
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.INVALID_PATH,
                message=f"Path for {logical_ref!r} must be a directory: {path_ref}",
                field=logical_ref,
            )
        )
        return None, tuple(errors), tuple(warnings)

    metadata, metadata_error = read_artifact_metadata(path)
    if metadata_error is not None:
        return None, (metadata_error,), tuple(warnings)
    assert metadata is not None

    artifact_type, meta_errors, meta_warnings = validate_artifact_metadata(
        metadata,
        logical_ref=logical_ref,
        request=request,
    )
    warnings.extend(meta_warnings)
    if meta_errors:
        return None, meta_errors, tuple(warnings)

    assert artifact_type is not None
    if expected_type is not None and artifact_type is not expected_type:
        errors.append(
            ArtifactResolutionError(
                code=ArtifactResolutionErrorCode.INCOMPATIBLE_ARTIFACT,
                message=(
                    f"Expected {expected_type.value} for {logical_ref!r}, "
                    f"got {artifact_type.value}."
                ),
                field=logical_ref,
            )
        )
        return None, tuple(errors), tuple(warnings)

    fingerprint = fingerprint_provider.digest_for_path(path)
    expected_fp = metadata.get("fingerprint")
    expected_fp_str = expected_fp if isinstance(expected_fp, str) else None
    fp_error, fp_warning = fingerprint_provider.verify_expected(
        expected=expected_fp_str,
        actual=fingerprint,
        policy=fingerprint_policy,
        field=logical_ref,
    )
    if fp_error is not None:
        errors.append(fp_error)
        return None, tuple(errors), tuple(warnings)
    if fp_warning is not None:
        warnings.append(fp_warning)

    descriptor = ArtifactDescriptor(
        artifact_type=artifact_type,
        logical_ref=logical_ref,
        location_digest=fingerprint.value,
        metadata=metadata,
        fingerprint=fingerprint,
    )
    return descriptor, tuple(errors), tuple(warnings)
