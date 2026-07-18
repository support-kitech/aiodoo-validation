"""Unit tests for Phase 4 coding validation profile."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiodoo_validation.domain.artifacts import (
    ArtifactBundle,
    ArtifactDescriptor,
    ArtifactFingerprint,
)
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import (
    ArtifactType,
    ExecutionTier,
    ExitStatus,
    FingerprintPolicy,
    ProfileErrorCode,
    StageStatus,
    ValidationStage,
)
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.profiles.coding.compatibility import validate_coding_artifact_compatibility
from aiodoo_validation.profiles.coding.plan_builder import build_coding_validation_plan
from aiodoo_validation.profiles.coding.profile import CodingProfile
from aiodoo_validation.profiles.engine import ProfileEngine
from aiodoo_validation.profiles.resolver import ProfileResolver
from aiodoo_validation.resolution.filesystem import FilesystemArtifactResolver

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def _request(*, base: str, adapter: str, profile: str = "coding") -> ValidationRequest:
    return ValidationRequest(
        profile_name=profile,
        base_model_ref=base,
        adapter_ref=adapter,
        execution_tier=ExecutionTier.STANDARD,
        run_id="profile-test",
    )


def _context(request: ValidationRequest) -> RunContext:
    return RunContext.begin(request)


def _bundle(
    *,
    adapter_metadata: dict[str, object] | None = None,
    base_metadata: dict[str, object] | None = None,
) -> ArtifactBundle:
    fp = ArtifactFingerprint(value="placeholder:test", placeholder=True)
    return ArtifactBundle(
        base_model=ArtifactDescriptor(
            artifact_type=ArtifactType.BASE_MODEL,
            logical_ref="base_model",
            location_digest=fp.value,
            metadata=base_metadata or {"model_family": "qwen", "identifier": "qwen3-8b"},
            fingerprint=fp,
        ),
        adapter=ArtifactDescriptor(
            artifact_type=ArtifactType.CODING_ADAPTER,
            logical_ref="adapter",
            location_digest="placeholder:adapter",
            metadata=adapter_metadata or {"adapter_type": "coding"},
            fingerprint=ArtifactFingerprint(value="placeholder:adapter", placeholder=True),
        ),
        merged_model=None,
        protocol_major=1,
        protocol_minor=0,
        fingerprint_policy=FingerprintPolicy.OFF,
        bundle_digest="bundle-test",
    )


def test_profile_resolver_creates_coding_profile() -> None:
    request = _request(base="a", adapter="b")
    profile, error = ProfileResolver().resolve("coding", context=_context(request))
    assert error is None
    assert profile is not None
    assert isinstance(profile, CodingProfile)
    assert profile.profile_name == "coding"
    assert "qwen" in profile.supported_model_families


def test_profile_resolver_creates_adapter_profiles() -> None:
    request = _request(base="a", adapter="b")
    for name in ("planner", "repair", "conversation", "execution", "approval", "evaluation"):
        profile, error = ProfileResolver().resolve(name, context=_context(request))
        assert error is None
        assert profile is not None
        assert profile.profile_name == name


def test_profile_resolver_rejects_unsupported_profiles() -> None:
    request = _request(base="a", adapter="b")
    for name in ("merged", "foundation", "unknown"):
        profile, error = ProfileResolver().resolve(name, context=_context(request))
        assert profile is None
        assert error is not None
        assert error.code is ProfileErrorCode.UNSUPPORTED_PROFILE


def test_coding_compatibility_rejects_planner_adapter() -> None:
    bundle = _bundle(adapter_metadata={"adapter_type": "planner"})
    errors = validate_coding_artifact_compatibility(bundle)
    assert any(error.code is ProfileErrorCode.UNSUPPORTED_ADAPTER for error in errors)


def test_coding_compatibility_accepts_valid_bundle() -> None:
    errors = validate_coding_artifact_compatibility(_bundle())
    assert not errors


def test_validation_plan_is_immutable_and_metadata_only() -> None:
    request = _request(base="a", adapter="b")
    context = _context(request)
    profile = CodingProfile.create(odoo_versions=(17, 18))
    plan = build_coding_validation_plan(profile, bundle=_bundle(), context=context)

    assert plan.profile_name == "coding"
    assert plan.capabilities.supports_inference is True
    assert plan.capabilities.supports_oracles is True
    assert plan.capabilities.supports_scoring is True
    assert plan.capabilities.supports_benchmark is True
    assert plan.capabilities.supports_certification is True
    assert plan.capabilities.supports_reports is True
    assert plan.validation_stages == (ValidationStage.RUN_VALIDATION,)
    assert ValidationStage.INITIALIZE_INFERENCE in plan.execution_order
    assert plan.oracle_pipeline[0].enabled is True
    assert plan.oracle_pipeline[0].stage_id == "coding.oracle.metadata"
    assert plan.oracle_pipeline[-1].stage_id == "coding.oracle.quality"
    assert plan.oracle_pipeline[-1].enabled is False
    assert plan.scoring_pipeline[0].stage_id == "coding.score.metadata"
    assert plan.scoring_pipeline[0].enabled is True
    assert plan.scoring_pipeline[-1].enabled is False
    assert plan.benchmark_pipeline[0].stage_id == "coding.benchmark.metadata"
    assert plan.benchmark_pipeline[0].enabled is True
    assert plan.benchmark_pipeline[-1].enabled is False
    assert plan.certification_pipeline[0].stage_id == "coding.certification.metadata"
    assert plan.certification_pipeline[0].enabled is True
    assert plan.certification_pipeline[-1].enabled is False
    assert plan.report_pipeline[0].stage_id == "coding.report.metadata"
    assert plan.report_pipeline[0].enabled is True
    assert plan.report_pipeline[-1].enabled is False

    with pytest.raises(FrozenInstanceError):
        plan.plan_digest = "changed"  # type: ignore[misc]


def test_profile_engine_builds_plan_and_attaches_metadata() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    resolved = FilesystemArtifactResolver.create_default().resolve(_context(request))
    assert resolved.success and resolved.bundle is not None

    context = _context(request).with_artifact_bundle(resolved.bundle)
    outcome = ProfileEngine.create_default().resolve_profile(context)

    assert outcome.success is True
    assert outcome.profile is not None
    assert outcome.plan is not None
    assert outcome.plan.profile_name == "coding"
    assert outcome.plan.configuration["bundle_digest"] == resolved.bundle.bundle_digest


def test_profile_engine_missing_bundle_fails_gracefully() -> None:
    outcome = ProfileEngine.create_default().resolve_profile(
        _context(_request(base="a", adapter="b"))
    )
    assert outcome.success is False
    assert outcome.errors[0].code is ProfileErrorCode.MISSING_BUNDLE


def test_engine_attaches_profile_and_plan() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "coding_adapter"),
    )
    result = ValidationEngine.with_stubs().run(request)

    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.validation_profile is not None
    assert result.run_context.validation_plan is not None
    assert result.run_context.validation_profile.profile_name == "coding"
    profile_stage = result.run_context.placeholder_results[ValidationStage.RESOLVE_PROFILE]
    assert profile_stage.status is StageStatus.SUCCEEDED
    assert profile_stage.data.get("plan_digest") is not None


def test_engine_profile_failure_does_not_crash() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "planner_adapter"),
    )
    result = ValidationEngine.with_filesystem().run(request)

    assert result.exit_status is ExitStatus.FAILED
    assert result.run_context.validation_profile is None
    assert result.run_context.validation_plan is None
    assert ValidationStage.INITIALIZE_INFERENCE not in {
        record.stage for record in result.run_context.stage_records
    }


def test_planner_adapter_passes_resolution_but_fails_coding_profile() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "planner_adapter"),
    )
    artifact = FilesystemArtifactResolver.create_default().resolve(_context(request))
    assert artifact.success is True

    profile = ProfileEngine.create_default().resolve_profile(
        _context(request).with_artifact_bundle(artifact.bundle)  # type: ignore[arg-type]
    )
    assert profile.success is False
    assert profile.errors[0].code is ProfileErrorCode.UNSUPPORTED_ADAPTER


def test_planner_profile_accepts_planner_adapter() -> None:
    request = _request(
        base=str(FIXTURES / "base_model"),
        adapter=str(FIXTURES / "planner_adapter"),
        profile="planner",
    )
    artifact = FilesystemArtifactResolver.create_default().resolve(_context(request))
    assert artifact.success is True
    profile = ProfileEngine.create_default().resolve_profile(
        _context(request).with_artifact_bundle(artifact.bundle)  # type: ignore[arg-type]
    )
    assert profile.success is True
    assert profile.profile is not None
    assert profile.profile.profile_name == "planner"
