"""Unit tests for Phase 11 Public Integration API."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from aiodoo_validation import ValidationService, __version__
from aiodoo_validation.api import (
    build_coding_request,
    build_planner_request,
    capability_labels,
    colab_integration_hints,
    get_profile_info,
    get_repository_metadata,
    is_certified,
    is_execution_tier_supported,
    is_odoo_version_supported,
    is_profile_supported,
    is_protocol_supported,
    is_successful,
    list_profiles,
    model_repository_integration_hints,
    parse_odoo_versions,
    report_execution,
    stage_statuses,
    summarize_for_promotion,
    training_integration_hints,
    vscode_integration_hints,
)
from aiodoo_validation.domain.enums import ExecutionTier, ExitStatus, ValidationStage
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "aiodoo_validation"
API_DIR = PACKAGE / "api"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def test_repository_metadata_exposes_version_and_protocol() -> None:
    metadata = get_repository_metadata()
    assert metadata.repository_name == "aiodoo-validation"
    assert metadata.repository_version == __version__
    assert metadata.protocol.major == 1
    assert metadata.protocol.version_label == "1.0"
    assert "coding" in metadata.supported_profiles
    assert "standard" in metadata.supported_execution_tiers
    assert ValidationStage.REPORT in metadata.pipeline_stages


def test_profile_discovery_lists_supported_profiles() -> None:
    profiles = list_profiles()
    assert "coding" in profiles
    assert "planner" in profiles
    assert "repair" in profiles
    profile = get_profile_info("coding")
    assert profile.profile_name == "coding"
    assert profile.supported_runtimes
    assert profile.capabilities.supports_reports is True
    assert ValidationStage.REPORT in profile.pipeline_stages
    assert "supports_reports" in capability_labels(profile.capabilities)
    planner = get_profile_info("planner")
    assert planner.profile_name == "planner"


def test_compatibility_helpers() -> None:
    assert is_protocol_supported(1, 0) is True
    assert is_protocol_supported(2, 0) is False
    assert is_profile_supported("coding") is True
    assert is_profile_supported("planner") is True
    assert is_profile_supported("merged") is False
    assert is_odoo_version_supported(17) is True
    assert is_odoo_version_supported(99) is False
    assert is_execution_tier_supported("standard") is True
    assert is_execution_tier_supported("prod") is True
    assert is_execution_tier_supported("invalid") is False


def test_build_coding_request_and_parse_odoo_versions() -> None:
    request = build_coding_request(
        base_model_ref="base",
        adapter_ref="adapter",
        execution_tier="smoke",
        odoo_versions="17,18",
        metadata={"evaluation_corpus_id": "future.coding.eval"},
    )
    assert request.profile_name == "coding"
    assert request.execution_tier is ExecutionTier.SMOKE
    assert request.odoo_versions == (17, 18)
    assert request.metadata["evaluation_corpus_id"] == "future.coding.eval"
    assert parse_odoo_versions("17,18,19") == (17, 18, 19)


def test_build_planner_request() -> None:
    request = build_planner_request(
        base_model_ref="base",
        adapter_ref="adapter",
        execution_tier="smoke",
        odoo_versions="18",
        metadata={"evaluation_corpus_id": "planner.eval"},
    )
    assert request.profile_name == "planner"
    assert request.execution_tier is ExecutionTier.SMOKE
    assert request.odoo_versions == (18,)
    assert request.metadata["evaluation_corpus_id"] == "planner.eval"


def test_validation_service_runs_with_stubs() -> None:
    service = ValidationService.create_with_stubs()
    request = ValidationRequest(
        profile_name="coding",
        base_model_ref="base",
        adapter_ref="adapter",
    )
    result = service.validate(request)
    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    assert result.run_context.report_execution is not None


def test_validation_service_matches_engine_with_stubs() -> None:
    request = ValidationRequest(
        profile_name="coding",
        base_model_ref="base",
        adapter_ref="adapter",
    )
    service_result = ValidationService.create_with_stubs().validate(request)
    engine_result = ValidationEngine.with_stubs().run(request)
    assert service_result.exit_status == engine_result.exit_status


def test_result_helpers() -> None:
    request = ValidationRequest(
        profile_name="coding",
        base_model_ref=str(FIXTURES / "base_model"),
        adapter_ref=str(FIXTURES / "coding_adapter"),
    )
    result = ValidationService.create_default().validate(request)
    assert is_successful(result) is True
    assert is_certified(result) is False
    assert report_execution(result) is not None
    statuses = stage_statuses(result)
    assert statuses[ValidationStage.REPORT] is not None


def test_summarize_for_promotion() -> None:
    request = ValidationRequest(
        profile_name="coding",
        base_model_ref="base",
        adapter_ref="adapter",
    )
    result = ValidationService.create_with_stubs().validate(request)
    summary = summarize_for_promotion(result)
    assert summary["exit_status"] == ExitStatus.NOT_CERTIFIED.value
    assert summary["successful"] is True
    assert summary["certified"] is False
    assert summary["report_template_count"] == 7


def test_integration_hints_are_generic_strings() -> None:
    training = training_integration_hints()
    colab = colab_integration_hints()
    vscode = vscode_integration_hints()
    models = model_repository_integration_hints()
    assert "ValidationService" in training.import_statement
    assert "pip install" in colab.install_command
    assert vscode.command_id == "aiodoo.validateArtifacts"
    assert "report_execution" in models.report_field
    assert models.promotion_checklist


def test_api_does_not_import_ecosystem_repositories() -> None:
    forbidden_roots = {
        "aiodoo_training",
        "aiodoo_colab",
        "aiodoo_models",
        "aiodoo_vscode",
        "cursor",
        "vscode",
        "google",
        "torch",
        "transformers",
        "datasets",
        "trl",
        "peft",
        "accelerate",
    }
    violations: list[str] = []
    for path in API_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in forbidden_roots:
                        violations.append(f"{path.relative_to(ROOT)}: {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in forbidden_roots:
                    violations.append(f"{path.relative_to(ROOT)}: {node.module}")
    assert not violations, "api must not import ecosystem repositories:\n" + "\n".join(violations)


def test_api_does_not_import_upstream_execution_modules() -> None:
    forbidden_suffixes = (
        "oracles.engine",
        "oracles.registry",
        "scoring.engine",
        "benchmark.engine",
        "certification.engine",
        "reporting.engine",
    )
    violations: list[str] = []
    for path in API_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
                if module.endswith(forbidden_suffixes) or module in {
                    "aiodoo_validation.oracles",
                    "aiodoo_validation.scoring",
                    "aiodoo_validation.benchmark",
                    "aiodoo_validation.certification",
                    "aiodoo_validation.reporting",
                }:
                    violations.append(f"{path.relative_to(ROOT)}: {module}")
    assert not violations, "api must not import upstream execution modules:\n" + "\n".join(
        violations
    )


def test_unknown_profile_raises() -> None:
    with pytest.raises(ValueError):
        get_profile_info("merged")
