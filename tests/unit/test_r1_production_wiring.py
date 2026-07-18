"""Production wiring consistency — repair capability delivery chain (R1)."""

from __future__ import annotations

from aiodoo_validation.benchmark.production import default_production_benchmark_policies
from aiodoo_validation.certification.production import (
    default_production_certification_policies,
)
from aiodoo_validation.profiles.adapter_profile import AdapterProfile
from aiodoo_validation.reporting.production import default_production_report_templates
from aiodoo_validation.scoring.ids import REPAIR_SCORE_BEHAVIOR
from aiodoo_validation.scoring.production import default_production_score_policies


def test_repair_behavior_pipeline_and_registry_ids_align() -> None:
    profile = AdapterProfile.create("repair", odoo_versions=(18,))
    pipeline = {
        "oracle": [s.stage_id for s in profile.oracle_pipeline],
        "score": [s.stage_id for s in profile.scoring_pipeline],
        "benchmark": [s.stage_id for s in profile.benchmark_pipeline],
        "certification": [s.stage_id for s in profile.certification_pipeline],
        "report": [s.stage_id for s in profile.report_pipeline],
    }
    assert "repair.oracle.behavior.repair" in pipeline["oracle"]
    assert REPAIR_SCORE_BEHAVIOR in pipeline["score"]
    assert "repair.benchmark.behavior" in pipeline["benchmark"]
    assert "repair.certification.behavior" in pipeline["certification"]
    assert "repair.report.behavior" in pipeline["report"]

    score_ids = {p.metadata.policy_id for p in default_production_score_policies(profile="repair")}
    benches = {
        p.metadata.policy_id: p.metadata.source_score_policy_id
        for p in default_production_benchmark_policies(profile="repair")
    }
    certs = {
        p.metadata.policy_id: p.metadata.source_benchmark_policy_id
        for p in default_production_certification_policies(profile="repair")
    }
    reports = {
        t.metadata.template_id: t.metadata.source_certification_policy_id
        for t in default_production_report_templates(profile="repair")
    }

    assert REPAIR_SCORE_BEHAVIOR in score_ids
    assert benches["repair.benchmark.behavior"] == REPAIR_SCORE_BEHAVIOR
    assert certs["repair.certification.behavior"] == "repair.benchmark.behavior"
    assert reports["repair.report.behavior"] == "repair.certification.behavior"


def test_coding_profile_has_no_behavior_delivery_stages() -> None:
    profile = AdapterProfile.create("coding", odoo_versions=(18,))
    for stages in (
        profile.oracle_pipeline,
        profile.scoring_pipeline,
        profile.benchmark_pipeline,
        profile.certification_pipeline,
        profile.report_pipeline,
    ):
        assert not any("behavior" in stage.stage_id for stage in stages)
