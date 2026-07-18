"""Production wiring consistency — repair + coding capability delivery chains."""

from __future__ import annotations

from aiodoo_validation.benchmark.production import default_production_benchmark_policies
from aiodoo_validation.certification.ids import (
    CODING_CERTIFICATION_BEHAVIOR,
    PLANNER_CERTIFICATION_BEHAVIOR,
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
from aiodoo_validation.scoring.ids import (
    CODING_SCORE_BEHAVIOR,
    PLANNER_SCORE_BEHAVIOR,
    REPAIR_SCORE_BEHAVIOR,
)
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


def test_production_registers_repair_coding_and_planner_behavior_oracles() -> None:
    components = ProductionPipelineComponents.create()
    engine = components.oracle_runner
    registry = engine.registry
    assert registry.get("repair.oracle.behavior.repair") is not None
    assert registry.get(CODING_ORACLE_BEHAVIOR) is not None
    assert registry.get("planner.oracle.behavior.planner") is not None
    assert registry.get("conversation.oracle.behavior.conversation") is not None
    assert registry.get("execution.oracle.behavior.execution") is not None


def test_planner_behavior_pipeline_and_registry_ids_align() -> None:
    profile = AdapterProfile.create("planner", odoo_versions=(18,))
    pipeline = {
        "oracle": [s.stage_id for s in profile.oracle_pipeline],
        "score": [s.stage_id for s in profile.scoring_pipeline],
        "benchmark": [s.stage_id for s in profile.benchmark_pipeline],
        "certification": [s.stage_id for s in profile.certification_pipeline],
        "report": [s.stage_id for s in profile.report_pipeline],
    }
    assert "planner.oracle.behavior.planner" in pipeline["oracle"]
    assert PLANNER_SCORE_BEHAVIOR in pipeline["score"]
    assert "planner.benchmark.behavior" in pipeline["benchmark"]
    assert PLANNER_CERTIFICATION_BEHAVIOR in pipeline["certification"]
    assert "planner.report.behavior" in pipeline["report"]

    score_ids = {p.metadata.policy_id for p in default_production_score_policies(profile="planner")}
    benches = {
        p.metadata.policy_id: p.metadata.source_score_policy_id
        for p in default_production_benchmark_policies(profile="planner")
    }
    certs = {
        p.metadata.policy_id: p.metadata.source_benchmark_policy_id
        for p in default_production_certification_policies(profile="planner")
    }
    reports = {
        t.metadata.template_id: t.metadata.source_certification_policy_id
        for t in default_production_report_templates(profile="planner")
    }

    assert PLANNER_SCORE_BEHAVIOR in score_ids
    assert benches["planner.benchmark.behavior"] == PLANNER_SCORE_BEHAVIOR
    assert certs[PLANNER_CERTIFICATION_BEHAVIOR] == "planner.benchmark.behavior"
    assert reports["planner.report.behavior"] == PLANNER_CERTIFICATION_BEHAVIOR


def test_conversation_behavior_pipeline_and_registry_ids_align() -> None:
    from aiodoo_validation.certification.ids import CONVERSATION_CERTIFICATION_BEHAVIOR
    from aiodoo_validation.scoring.ids import CONVERSATION_SCORE_BEHAVIOR

    profile = AdapterProfile.create("conversation", odoo_versions=(18,))
    pipeline = {
        "oracle": [s.stage_id for s in profile.oracle_pipeline],
        "score": [s.stage_id for s in profile.scoring_pipeline],
        "benchmark": [s.stage_id for s in profile.benchmark_pipeline],
        "certification": [s.stage_id for s in profile.certification_pipeline],
        "report": [s.stage_id for s in profile.report_pipeline],
    }
    assert "conversation.oracle.behavior.conversation" in pipeline["oracle"]
    assert CONVERSATION_SCORE_BEHAVIOR in pipeline["score"]
    assert "conversation.benchmark.behavior" in pipeline["benchmark"]
    assert CONVERSATION_CERTIFICATION_BEHAVIOR in pipeline["certification"]
    assert "conversation.report.behavior" in pipeline["report"]

    score_ids = {
        p.metadata.policy_id for p in default_production_score_policies(profile="conversation")
    }
    benches = {
        p.metadata.policy_id: p.metadata.source_score_policy_id
        for p in default_production_benchmark_policies(profile="conversation")
    }
    certs = {
        p.metadata.policy_id: p.metadata.source_benchmark_policy_id
        for p in default_production_certification_policies(profile="conversation")
    }
    reports = {
        t.metadata.template_id: t.metadata.source_certification_policy_id
        for t in default_production_report_templates(profile="conversation")
    }

    assert CONVERSATION_SCORE_BEHAVIOR in score_ids
    assert benches["conversation.benchmark.behavior"] == CONVERSATION_SCORE_BEHAVIOR
    assert certs[CONVERSATION_CERTIFICATION_BEHAVIOR] == "conversation.benchmark.behavior"
    assert reports["conversation.report.behavior"] == CONVERSATION_CERTIFICATION_BEHAVIOR


def test_execution_behavior_pipeline_and_registry_ids_align() -> None:
    from aiodoo_validation.certification.ids import EXECUTION_CERTIFICATION_BEHAVIOR
    from aiodoo_validation.scoring.ids import EXECUTION_SCORE_BEHAVIOR

    profile = AdapterProfile.create("execution", odoo_versions=(18,))
    pipeline = {
        "oracle": [s.stage_id for s in profile.oracle_pipeline],
        "score": [s.stage_id for s in profile.scoring_pipeline],
        "benchmark": [s.stage_id for s in profile.benchmark_pipeline],
        "certification": [s.stage_id for s in profile.certification_pipeline],
        "report": [s.stage_id for s in profile.report_pipeline],
    }
    assert "execution.oracle.behavior.execution" in pipeline["oracle"]
    assert EXECUTION_SCORE_BEHAVIOR in pipeline["score"]
    assert "execution.benchmark.behavior" in pipeline["benchmark"]
    assert EXECUTION_CERTIFICATION_BEHAVIOR in pipeline["certification"]
    assert "execution.report.behavior" in pipeline["report"]

    score_ids = {
        p.metadata.policy_id for p in default_production_score_policies(profile="execution")
    }
    benches = {
        p.metadata.policy_id: p.metadata.source_score_policy_id
        for p in default_production_benchmark_policies(profile="execution")
    }
    certs = {
        p.metadata.policy_id: p.metadata.source_benchmark_policy_id
        for p in default_production_certification_policies(profile="execution")
    }
    reports = {
        t.metadata.template_id: t.metadata.source_certification_policy_id
        for t in default_production_report_templates(profile="execution")
    }

    assert EXECUTION_SCORE_BEHAVIOR in score_ids
    assert benches["execution.benchmark.behavior"] == EXECUTION_SCORE_BEHAVIOR
    assert certs[EXECUTION_CERTIFICATION_BEHAVIOR] == "execution.benchmark.behavior"
    assert reports["execution.report.behavior"] == EXECUTION_CERTIFICATION_BEHAVIOR
