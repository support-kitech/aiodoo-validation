"""Production wiring consistency — repair + coding capability delivery chains."""

from __future__ import annotations

from aiodoo_validation.benchmark.production import default_production_benchmark_policies
from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_BEHAVIOR,
    REPAIR_CERTIFICATION_BEHAVIOR,
)
from aiodoo_validation.certification.production import (
    default_production_certification_policies,
)
from aiodoo_validation.oracles.ids import CODING_ORACLE_BEHAVIOR
from aiodoo_validation.production import ProductionPipelineComponents
from aiodoo_validation.profiles.adapter_profile import AdapterProfile
from aiodoo_validation.profiles.coding.profile import CodingProfile
from aiodoo_validation.reporting.ids import CODING_REPORT_BEHAVIOR
from aiodoo_validation.reporting.production import default_production_report_templates
from aiodoo_validation.scoring.ids import CODING_SCORE_BEHAVIOR, REPAIR_SCORE_BEHAVIOR
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
    assert REPAIR_CERTIFICATION_BEHAVIOR in pipeline["certification"]
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
    assert certs[REPAIR_CERTIFICATION_BEHAVIOR] == "repair.benchmark.behavior"
    assert reports["repair.report.behavior"] == REPAIR_CERTIFICATION_BEHAVIOR


def test_coding_behavior_pipeline_and_registry_ids_align() -> None:
    profile = CodingProfile.create(odoo_versions=(18,))
    pipeline = {
        "oracle": [s.stage_id for s in profile.oracle_pipeline],
        "score": [s.stage_id for s in profile.scoring_pipeline],
        "benchmark": [s.stage_id for s in profile.benchmark_pipeline],
        "certification": [s.stage_id for s in profile.certification_pipeline],
        "report": [s.stage_id for s in profile.report_pipeline],
    }
    assert CODING_ORACLE_BEHAVIOR in pipeline["oracle"]
    assert CODING_SCORE_BEHAVIOR in pipeline["score"]
    assert "coding.benchmark.behavior" in pipeline["benchmark"]
    assert CODING_CERTIFICATION_BEHAVIOR in pipeline["certification"]
    assert CODING_REPORT_BEHAVIOR in pipeline["report"]

    score_ids = {p.metadata.policy_id for p in default_production_score_policies(profile="coding")}
    benches = {
        p.metadata.policy_id: p.metadata.source_score_policy_id
        for p in default_production_benchmark_policies(profile="coding")
    }
    certs = {
        p.metadata.policy_id: p.metadata.source_benchmark_policy_id
        for p in default_production_certification_policies(profile="coding")
    }
    reports = {
        t.metadata.template_id: t.metadata.source_certification_policy_id
        for t in default_production_report_templates(profile="coding")
    }

    assert CODING_SCORE_BEHAVIOR in score_ids
    assert benches["coding.benchmark.behavior"] == CODING_SCORE_BEHAVIOR
    assert certs[CODING_CERTIFICATION_BEHAVIOR] == "coding.benchmark.behavior"
    assert reports[CODING_REPORT_BEHAVIOR] == CODING_CERTIFICATION_BEHAVIOR


def test_production_registers_repair_and_coding_behavior_oracles() -> None:
    components = ProductionPipelineComponents.create()
    engine = components.oracle_runner
    registry = engine.registry
    assert registry.get("repair.oracle.behavior.repair") is not None
    assert registry.get(CODING_ORACLE_BEHAVIOR) is not None
