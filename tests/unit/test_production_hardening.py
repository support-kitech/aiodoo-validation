"""Integration-style tests for production report richness and tiers."""

from __future__ import annotations

from pathlib import Path

from aiodoo_validation.domain.enums import ExecutionTier, ExitStatus
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.engine import ValidationEngine
from aiodoo_validation.execution import (
    allows_certification,
    certification_label,
    is_framework_only_tier,
    normalize_execution_tier,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def test_production_report_includes_machine_readable_summary() -> None:
    request = ValidationRequest(
        profile_name="coding",
        base_model_ref=str(FIXTURES / "base_model"),
        adapter_ref=str(FIXTURES / "coding_adapter"),
        execution_tier=ExecutionTier.STANDARD,
        odoo_versions=(18,),
    )
    result = ValidationEngine.with_filesystem().run(request)
    assert result.exit_status is ExitStatus.NOT_CERTIFIED
    report = result.run_context.report_execution
    assert report is not None
    assert report.results
    first = report.results[0]
    assert first.metadata.get("machine_readable") is True
    assert first.metadata.get("execution_tier") == "standard"
    assert first.metadata.get("profile") == "coding"
    summary = first.metadata.get("run_summary")
    assert isinstance(summary, dict)
    assert "structural_validation" in summary
    assert "behavior_validation" in summary
    assert summary["behavior_validation"]["status"] == "deferred"
    assert summary["behavior_status"] == "deferred"
    assert summary["validation_kind"] == "structural"
    assert summary["certification_label"]
    assert summary["repository_version"]
    assert summary["report_version"] == "1.1.0"
    assert "score_summary" in summary
    assert "benchmark_summary" in summary
    assert "certification_decision" in summary
    assert "artifacts" in summary
    titles = {section.title for section in first.sections}
    assert "Structural Validation" in titles
    assert "Behavior Validation" in titles
    assert "Certification Decision" in titles


def test_planner_profile_production_path() -> None:
    request = ValidationRequest(
        profile_name="planner",
        base_model_ref=str(FIXTURES / "base_model"),
        adapter_ref=str(FIXTURES / "planner_adapter"),
        execution_tier=ExecutionTier.SMOKE,
        odoo_versions=(18,),
    )
    result = ValidationEngine.with_filesystem().run(request)
    assert result.exit_status is ExitStatus.COMPLETED
    assert result.run_context.validation_profile is not None
    assert result.run_context.validation_profile.profile_name == "planner"
    assert certification_label(profile_name="planner", certified=True) == "planner-certified"


def test_execution_tier_matrix() -> None:
    assert normalize_execution_tier("prod") is ExecutionTier.FULL
    assert is_framework_only_tier("standard")
    assert allows_certification("smoke")
    assert allows_certification("full")
    assert not allows_certification("standard")
