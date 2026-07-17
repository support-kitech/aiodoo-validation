"""Unit tests for Phase 2 artifact resolution."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiodoo_validation.domain.artifacts import (
    ArtifactBundle,
    ArtifactDescriptor,
    ArtifactFingerprint,
)
from aiodoo_validation.domain.enums import (
    ArtifactResolutionErrorCode,
    ArtifactType,
    ExecutionTier,
    ExitStatus,
    FingerprintPolicy,
    StageStatus,
    SupportedValidationProfile,
    ValidationStage,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.resolution import ArtifactResolutionOutcome
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.resolution.common import build_artifact_bundle, resolve_descriptor
from aiodoo_validation.resolution.filesystem import FilesystemArtifactResolver
from aiodoo_validation.resolution.fingerprint import PlaceholderFingerprintProvider
from aiodoo_validation.resolution.stub_resolver import StubArtifactResolver

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def _has_error(outcome: ArtifactResolutionOutcome, code: ArtifactResolutionErrorCode) -> bool:
    return any(error.code is code for error in outcome.errors)


def _request(
    *,
    base: str,
    adapter: str,
    merged: str | None = None,
    fingerprint_policy: FingerprintPolicy = FingerprintPolicy.OFF,
    strict_fingerprint_policy: bool = False,
) -> ValidationRequest:
    return ValidationRequest(
        profile_name=SupportedValidationProfile.CODING.value,
        base_model_ref=base,
        adapter_ref=adapter,
        merged_model_ref=merged,
        execution_tier=ExecutionTier.STANDARD,
        fingerprint_policy=fingerprint_policy,
        strict_fingerprint_policy=strict_fingerprint_policy,
        run_id="artifact-test",
    )


def _context(request: ValidationRequest):
    from aiodoo_validation.domain.context import RunContext

    return RunContext.begin(request)


def test_filesystem_resolver_valid_artifacts() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    resolver = FilesystemArtifactResolver.create_default()
    outcome = resolver.resolve(_context(request))

    assert outcome.success is True
    assert outcome.bundle is not None
    assert outcome.bundle.base_model.artifact_type is ArtifactType.BASE_MODEL
    assert outcome.bundle.adapter.artifact_type is ArtifactType.CODING_ADAPTER
    assert outcome.bundle.merged_model is None
    assert outcome.bundle.base_model.logical_ref == "base_model"
    assert "placeholder:" in outcome.bundle.base_model.location_digest


def test_filesystem_resolver_with_merged_model_placeholder() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
        merged=str(FIXTURES / "merged_model"),
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is True
    assert outcome.bundle is not None
    assert outcome.bundle.merged_model is not None
    assert outcome.bundle.merged_model.artifact_type is ArtifactType.MERGED_MODEL


def test_missing_path_returns_structured_error() -> None:
    request = _request(
        base=str(FIXTURES / "does-not-exist"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is False
    assert outcome.bundle is None
    assert _has_error(outcome, ArtifactResolutionErrorCode.MISSING_PATH)


def test_invalid_path_file_not_directory() -> None:
    file_path = FIXTURES / "base_model" / "artifact.json"
    request = _request(
        base=str(file_path),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is False
    assert _has_error(outcome, ArtifactResolutionErrorCode.INVALID_PATH)


def test_missing_metadata() -> None:
    empty_dir = FIXTURES / "empty_dir"
    empty_dir.mkdir(exist_ok=True)
    request = _request(base=str(empty_dir), adapter=str(FIXTURES / "coding_adapter"))
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is False
    assert _has_error(outcome, ArtifactResolutionErrorCode.MISSING_METADATA)


def test_invalid_metadata_json() -> None:
    request = _request(
        base=str(FIXTURES / "invalid_metadata"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is False
    assert _has_error(outcome, ArtifactResolutionErrorCode.MISSING_METADATA)


def test_unsupported_planner_adapter_resolves_but_profile_rejects() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "planner_adapter"),
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is True
    assert outcome.bundle is not None


@pytest.mark.parametrize(
    "adapter_type",
    ["repair", "conversation", "execution"],
)
def test_rejected_adapter_types_resolve_at_artifact_stage(adapter_type: str) -> None:
    adapter_dir = FIXTURES / f"temp_{adapter_type}_adapter"
    adapter_dir.mkdir(exist_ok=True)
    (adapter_dir / "artifact.json").write_text(
        json.dumps(
            {
                "artifact_type": "coding_adapter",
                "protocol_major": 1,
                "identifier": f"temp-{adapter_type}",
                "adapter_type": adapter_type,
            }
        ),
        encoding="utf-8",
    )
    request = _request(base=str(FIXTURES / "base_model"), adapter=str(adapter_dir))
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is True


def test_invalid_protocol_version() -> None:
    bad_dir = FIXTURES / "bad_protocol"
    bad_dir.mkdir(exist_ok=True)
    (bad_dir / "artifact.json").write_text(
        json.dumps(
            {
                "artifact_type": "base_model",
                "protocol_major": 99,
                "identifier": "bad-protocol",
            }
        ),
        encoding="utf-8",
    )
    request = _request(base=str(bad_dir), adapter=str(FIXTURES / "coding_adapter"))
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is False
    assert _has_error(outcome, ArtifactResolutionErrorCode.INVALID_PROTOCOL)


def test_duplicate_artifact_locations() -> None:
    from aiodoo_validation.resolution.compatibility import validate_no_duplicate_locations

    fp = ArtifactFingerprint(value="placeholder:same", placeholder=True)
    first = ArtifactDescriptor(
        artifact_type=ArtifactType.BASE_MODEL,
        logical_ref="base_model",
        location_digest=fp.value,
        fingerprint=fp,
    )
    second = ArtifactDescriptor(
        artifact_type=ArtifactType.CODING_ADAPTER,
        logical_ref="adapter",
        location_digest=fp.value,
        fingerprint=fp,
    )
    errors = validate_no_duplicate_locations((first, second))

    assert len(errors) == 1
    assert errors[0].code is ArtifactResolutionErrorCode.DUPLICATE_ARTIFACT


def test_fingerprint_strict_mode_fails_on_mismatch() -> None:
    strict_dir = FIXTURES / "strict_fp"
    strict_dir.mkdir(exist_ok=True)
    (strict_dir / "artifact.json").write_text(
        json.dumps(
            {
                "artifact_type": "base_model",
                "protocol_major": 1,
                "identifier": "strict-fp",
                "fingerprint": "placeholder:expected-mismatch",
            }
        ),
        encoding="utf-8",
    )
    request = _request(
        base=str(strict_dir),
        adapter=str(FIXTURES / "coding_adapter"),
        fingerprint_policy=FingerprintPolicy.STRICT,
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is False
    assert _has_error(outcome, ArtifactResolutionErrorCode.FINGERPRINT_MISMATCH)


def test_fingerprint_warn_mode_continues_with_warning() -> None:
    warn_dir = FIXTURES / "warn_fp"
    warn_dir.mkdir(exist_ok=True)
    (warn_dir / "artifact.json").write_text(
        json.dumps(
            {
                "artifact_type": "base_model",
                "protocol_major": 1,
                "identifier": "warn-fp",
                "fingerprint": "placeholder:expected-mismatch",
            }
        ),
        encoding="utf-8",
    )
    request = _request(
        base=str(warn_dir),
        adapter=str(FIXTURES / "coding_adapter"),
        fingerprint_policy=FingerprintPolicy.WARN,
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is True
    assert outcome.warnings


def test_fingerprint_off_mode_ignores_expected() -> None:
    off_dir = FIXTURES / "off_fp"
    off_dir.mkdir(exist_ok=True)
    (off_dir / "artifact.json").write_text(
        json.dumps(
            {
                "artifact_type": "base_model",
                "protocol_major": 1,
                "identifier": "off-fp",
                "fingerprint": "placeholder:expected-mismatch",
            }
        ),
        encoding="utf-8",
    )
    request = _request(
        base=str(off_dir),
        adapter=str(FIXTURES / "coding_adapter"),
        fingerprint_policy=FingerprintPolicy.OFF,
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is True
    assert not outcome.warnings


def test_strict_fingerprint_policy_flag() -> None:
    strict_dir = FIXTURES / "strict_flag_fp"
    strict_dir.mkdir(exist_ok=True)
    (strict_dir / "artifact.json").write_text(
        json.dumps(
            {
                "artifact_type": "base_model",
                "protocol_major": 1,
                "identifier": "strict-flag",
                "fingerprint": "placeholder:wrong",
            }
        ),
        encoding="utf-8",
    )
    request = _request(
        base=str(strict_dir),
        adapter=str(FIXTURES / "coding_adapter"),
        strict_fingerprint_policy=True,
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))

    assert outcome.success is False
    assert _has_error(outcome, ArtifactResolutionErrorCode.FINGERPRINT_MISMATCH)


def test_artifact_bundle_is_immutable() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))
    assert outcome.bundle is not None

    with pytest.raises(FrozenInstanceError):
        outcome.bundle.bundle_digest = "changed"  # type: ignore[misc]


def test_descriptor_does_not_expose_raw_path() -> None:
    base_path = FIXTURES / "base_model"
    request = _request(base=str(base_path), adapter=str(FIXTURES / "coding_adapter"))
    outcome = FilesystemArtifactResolver.create_default().resolve(_context(request))
    assert outcome.bundle is not None

    descriptor_repr = repr(outcome.bundle.base_model)
    assert str(base_path) not in descriptor_repr
    assert outcome.bundle.base_model.location_digest.startswith("placeholder:")


def test_stub_resolver_builds_bundle() -> None:
    request = _request(base="stub/base", adapter="stub/adapter")
    outcome = StubArtifactResolver().resolve(_context(request))

    assert outcome.success is True
    assert outcome.bundle is not None
    assert outcome.bundle.metadata["stub"] is True


def test_engine_filesystem_success_attaches_bundle() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    result = ValidationEngine.with_filesystem().run(request)

    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.artifact_bundle is not None
    artifact_stage = result.run_context.placeholder_results[ValidationStage.RESOLVE_ARTIFACTS]
    assert artifact_stage.status is StageStatus.SUCCEEDED


def test_engine_artifact_failure_does_not_crash() -> None:
    request = _request(
        base=str(FIXTURES / "missing"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    result = ValidationEngine.with_filesystem().run(request)

    assert result.exit_status is ExitStatus.FAILED
    assert result.run_context.artifact_bundle is None
    assert result.run_context.errors
    artifact_stage = result.run_context.placeholder_results[ValidationStage.RESOLVE_ARTIFACTS]
    assert artifact_stage.status is StageStatus.FAILED
    executed = {record.stage for record in result.run_context.stage_records}
    assert ValidationStage.INITIALIZE_INFERENCE not in executed


def test_build_artifact_bundle_digest_stable() -> None:
    fp = ArtifactFingerprint(value="placeholder:aaa", placeholder=True)
    base = ArtifactDescriptor(
        artifact_type=ArtifactType.BASE_MODEL,
        logical_ref="base_model",
        location_digest=fp.value,
        fingerprint=fp,
    )
    adapter = ArtifactDescriptor(
        artifact_type=ArtifactType.CODING_ADAPTER,
        logical_ref="adapter",
        location_digest="placeholder:bbb",
        fingerprint=ArtifactFingerprint(value="placeholder:bbb", placeholder=True),
    )
    request = _request(base="a", adapter="b")
    bundle = build_artifact_bundle(
        request,
        base_model=base,
        adapter=adapter,
        merged_model=None,
        fingerprint_policy=FingerprintPolicy.OFF,
    )
    assert isinstance(bundle, ArtifactBundle)
    assert len(bundle.bundle_digest) == 16


def test_resolve_descriptor_empty_path() -> None:
    request = _request(base="x", adapter="y")
    provider = PlaceholderFingerprintProvider()
    descriptor, errors, _warnings = resolve_descriptor(
        logical_ref="base_model",
        path_ref="   ",
        expected_type=ArtifactType.BASE_MODEL,
        request=request,
        fingerprint_provider=provider,
        fingerprint_policy=FingerprintPolicy.OFF,
    )
    assert descriptor is None
    assert errors[0].code is ArtifactResolutionErrorCode.MISSING_PATH
