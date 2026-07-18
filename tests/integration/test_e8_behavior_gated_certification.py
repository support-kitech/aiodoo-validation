"""E8 behavior-gated certification integration tests."""

from __future__ import annotations

from types import MappingProxyType

from aiodoo_validation.benchmark.production import default_production_benchmark_policies
from aiodoo_validation.certification.behavioral import BehaviorGatedCertificationPolicy
from aiodoo_validation.certification.criteria import (
    CertificationCriteria,
    default_behavior_gated_certification_criteria,
    default_structural_certification_criteria,
    evaluate_certification_criteria,
)
from aiodoo_validation.certification.ids import REPAIR_CERTIFICATION_BEHAVIOR
from aiodoo_validation.certification.production import (
    default_production_certification_policies,
)
from aiodoo_validation.certification.score_signals import (
    extract_behavioral_score_signals,
)
from aiodoo_validation.domain.benchmark import (
    BenchmarkExecutionResult,
    BenchmarkResult,
)
from aiodoo_validation.domain.certification import CertificationContext
from aiodoo_validation.domain.enums import ExecutionTier, ValidationKind
from aiodoo_validation.domain.scoring import ScoreExecutionResult, ScoreResult
from aiodoo_validation.profiles.adapter_profile import AdapterProfile
from aiodoo_validation.reporting.production import default_production_report_templates
from aiodoo_validation.scoring.ids import REPAIR_SCORE_BEHAVIOR


def _behavior_score(
    *,
    deferred: bool = False,
    behavior: float | None = 100.0,
    transform: float | None = 100.0,
    weighted: float | None = None,
    score: float | None = None,
) -> ScoreResult:
    extras = {}
    if transform is not None:
        extras["transform_correctness"] = transform
    if weighted is None:
        if behavior is not None and transform is not None:
            weighted = (behavior + transform) / 2.0
        elif behavior is not None:
            weighted = behavior
        elif transform is not None:
            weighted = transform
        else:
            weighted = 0.0 if deferred else None
    primary = score if score is not None else (0.0 if weighted is None else weighted)
    return ScoreResult(
        policy_id=REPAIR_SCORE_BEHAVIOR,
        source_oracle_id="repair.oracle.behavior.repair",
        success=True,
        score=float(primary),
        message="test",
        metadata=MappingProxyType(
            {
                "deferred": deferred,
                "validation_kind": ValidationKind.BEHAVIORAL.value,
                "dimensions": {
                    "behavior": behavior,
                    "weighted": weighted,
                    "extras": extras,
                    "validation_kind": ValidationKind.BEHAVIORAL.value,
                },
                "pass_rate": behavior,
                "transforms_passed": (None if transform is None else transform >= 100.0),
            }
        ),
    )


def _score_execution(*scores: ScoreResult) -> ScoreExecutionResult:
    return ScoreExecutionResult(
        plan_digest="d",
        profile_name="repair",
        results=scores,
        duration_ms=1,
        policy_count=len(scores),
        success_count=len(scores),
        failure_count=0,
        aggregate_score=scores[0].score if scores else None,
    )


def _benchmark_from_score(score: ScoreResult) -> BenchmarkResult:
    passed = float(score.score) >= 100.0 and not bool(score.metadata.get("deferred"))
    return BenchmarkResult(
        policy_id="repair.benchmark.behavior",
        source_score_policy_id=REPAIR_SCORE_BEHAVIOR,
        success=True,
        benchmark_score=float(score.score),
        benchmark_pass=passed,
        benchmark_rank=1 if passed else 2,
        message="bench",
        metadata=MappingProxyType(
            {
                "dimensions": score.metadata.get("dimensions"),
                "threshold": 100.0,
            }
        ),
    )


def _cert_context(
    score: ScoreResult | None,
    *,
    tier: ExecutionTier = ExecutionTier.SMOKE,
    criteria: CertificationCriteria | None = None,
) -> tuple[BehaviorGatedCertificationPolicy, CertificationContext]:
    policy = BehaviorGatedCertificationPolicy.create_for_repair(criteria=criteria)
    if score is None:
        bench = BenchmarkResult(
            policy_id="repair.benchmark.behavior",
            source_score_policy_id=REPAIR_SCORE_BEHAVIOR,
            success=True,
            benchmark_score=0.0,
            benchmark_pass=False,
            benchmark_rank=2,
            message="missing",
        )
        score_exec = _score_execution()
    else:
        bench = _benchmark_from_score(score)
        score_exec = _score_execution(score)
    bench_exec = BenchmarkExecutionResult(
        plan_digest="d",
        profile_name="repair",
        results=(bench,),
        duration_ms=1,
        policy_count=1,
        success_count=1,
        failure_count=0,
    )
    context = CertificationContext(
        run_id="r1",
        profile_name="repair",
        plan_digest="d",
        protocol_major=1,
        protocol_minor=0,
        execution_tier=tier,
        benchmark_result=bench,
        benchmark_execution=bench_exec,
        score_execution=score_exec,
    )
    return policy, context


class TestCriteriaReasons:
    def test_structural_pass(self) -> None:
        evaluation = evaluate_certification_criteria(
            default_structural_certification_criteria(),
            execution_tier=ExecutionTier.SMOKE,
            structural_pass=True,
            benchmark_pass=True,
            oracle_score=100.0,
            benchmark_score=100.0,
        )
        assert evaluation.certified is True
        assert evaluation.reasons == ("criteria_satisfied",)

    def test_structural_failed(self) -> None:
        evaluation = evaluate_certification_criteria(
            default_structural_certification_criteria(),
            execution_tier=ExecutionTier.SMOKE,
            structural_pass=False,
            benchmark_pass=False,
            oracle_score=0.0,
            benchmark_score=0.0,
        )
        assert evaluation.certified is False
        assert "structural_failed" in evaluation.reasons

    def test_behavior_deferred(self) -> None:
        evaluation = evaluate_certification_criteria(
            default_behavior_gated_certification_criteria(),
            execution_tier=ExecutionTier.FULL,
            behavior_pass=None,
            behavior_deferred=True,
            benchmark_pass=False,
            benchmark_score=0.0,
        )
        assert evaluation.certified is False
        assert "behavior_deferred" in evaluation.reasons

    def test_behavior_failed(self) -> None:
        evaluation = evaluate_certification_criteria(
            default_behavior_gated_certification_criteria(),
            execution_tier=ExecutionTier.FULL,
            behavior_pass=False,
            behavior_deferred=False,
            behavior_score=40.0,
            transform_score=100.0,
            benchmark_pass=False,
            benchmark_score=40.0,
        )
        assert "behavior_failed" in evaluation.reasons
        assert "behavior_score_below_threshold" in evaluation.reasons

    def test_transform_failed(self) -> None:
        evaluation = evaluate_certification_criteria(
            default_behavior_gated_certification_criteria(),
            execution_tier=ExecutionTier.FULL,
            behavior_pass=True,
            behavior_score=100.0,
            transform_score=0.0,
            benchmark_pass=True,
            benchmark_score=100.0,
        )
        assert evaluation.certified is False
        assert "transform_failed" in evaluation.reasons

    def test_score_below_threshold(self) -> None:
        criteria = CertificationCriteria(
            require_behavior_pass=False,
            require_structural_pass=False,
            require_benchmark_pass=False,
            min_oracle_score=None,
            min_behavior_score=90.0,
            min_transform_score=None,
            min_benchmark_score=None,
        )
        evaluation = evaluate_certification_criteria(
            criteria,
            execution_tier=ExecutionTier.SMOKE,
            behavior_score=80.0,
        )
        assert "behavior_score_below_threshold" in evaluation.reasons

    def test_threshold_satisfied(self) -> None:
        evaluation = evaluate_certification_criteria(
            default_behavior_gated_certification_criteria(),
            execution_tier=ExecutionTier.SMOKE,
            behavior_pass=True,
            behavior_deferred=False,
            behavior_score=100.0,
            transform_score=100.0,
            benchmark_pass=True,
            benchmark_score=100.0,
        )
        assert evaluation.certified is True


class TestBehaviorGatedPolicy:
    def test_behavior_pass(self) -> None:
        policy, context = _cert_context(
            _behavior_score(behavior=100.0, transform=100.0, score=100.0)
        )
        result = policy.certify(context)
        assert result.certified is True
        assert result.metadata["criteria_reasons"] == ("criteria_satisfied",)
        assert result.metadata["behavior_gated"] is True

    def test_behavior_fail(self) -> None:
        policy, context = _cert_context(_behavior_score(behavior=0.0, transform=100.0, score=50.0))
        result = policy.certify(context)
        assert result.certified is False
        assert "behavior_failed" in result.metadata["criteria_reasons"]

    def test_deferred_corpus(self) -> None:
        policy, context = _cert_context(
            _behavior_score(
                deferred=True,
                behavior=None,
                transform=None,
                weighted=None,
                score=0.0,
            )
        )
        result = policy.certify(context)
        assert result.certified is False
        assert result.certification_level == "NOT_CERTIFIED"
        assert "behavior_deferred" in result.metadata["criteria_reasons"]

    def test_transform_failure(self) -> None:
        policy, context = _cert_context(_behavior_score(behavior=100.0, transform=0.0, score=50.0))
        result = policy.certify(context)
        assert result.certified is False
        assert "transform_failed" in result.metadata["criteria_reasons"]

    def test_score_below_threshold_custom_policy(self) -> None:
        criteria = CertificationCriteria(
            require_structural_pass=False,
            require_behavior_pass=True,
            require_benchmark_pass=False,
            min_oracle_score=None,
            min_behavior_score=95.0,
            min_transform_score=100.0,
            min_benchmark_score=None,
        )
        policy, context = _cert_context(
            _behavior_score(behavior=90.0, transform=100.0, score=90.0),
            criteria=criteria,
        )
        result = policy.certify(context)
        assert result.certified is False
        assert "behavior_score_below_threshold" in result.metadata["criteria_reasons"]

    def test_threshold_satisfied_custom_policy(self) -> None:
        criteria = CertificationCriteria(
            require_structural_pass=False,
            require_behavior_pass=False,
            require_benchmark_pass=False,
            min_oracle_score=None,
            min_behavior_score=80.0,
            min_transform_score=80.0,
            min_benchmark_score=None,
        )
        policy, context = _cert_context(
            _behavior_score(behavior=90.0, transform=85.0, score=90.0),
            criteria=criteria,
        )
        result = policy.certify(context)
        assert result.certified is True

    def test_policy_disabled_behavior_gate(self) -> None:
        criteria = CertificationCriteria(
            require_structural_pass=False,
            require_behavior_pass=False,
            require_benchmark_pass=False,
            min_oracle_score=None,
            min_behavior_score=None,
            min_transform_score=None,
            min_benchmark_score=None,
        )
        policy, context = _cert_context(
            _behavior_score(deferred=True, behavior=None, transform=None, score=0.0),
            criteria=criteria,
        )
        result = policy.certify(context)
        assert result.certified is True
        assert result.metadata["criteria_reasons"] == ("criteria_satisfied",)

    def test_missing_score_not_available(self) -> None:
        policy, context = _cert_context(None)
        result = policy.certify(context)
        assert result.certified is False
        assert "behavior_not_available" in result.metadata["criteria_reasons"]


class TestScoreSignalExtraction:
    def test_extracts_from_score_not_oracle(self) -> None:
        score = _behavior_score(behavior=75.0, transform=100.0)
        signals = extract_behavioral_score_signals(score)
        assert signals.behavior_score == 75.0
        assert signals.transform_score == 100.0
        assert signals.behavior_pass is False
        assert signals.deferred is False


class TestProfileRegistration:
    def test_repair_registers_behavior_chain(self) -> None:
        assert any(
            p.metadata.policy_id == "repair.benchmark.behavior"
            for p in default_production_benchmark_policies(profile="repair")
        )
        certs = default_production_certification_policies(profile="repair")
        assert any(p.metadata.policy_id == REPAIR_CERTIFICATION_BEHAVIOR for p in certs)
        reports = default_production_report_templates(profile="repair")
        assert any(t.metadata.template_id == "repair.report.behavior" for t in reports)

    def test_coding_registers_behavior_gate(self) -> None:
        from aiodoo_validation.certification.ids import CODING_CERTIFICATION_BEHAVIOR
        from aiodoo_validation.profiles.coding.profile import CodingProfile
        from aiodoo_validation.reporting.ids import CODING_REPORT_BEHAVIOR

        assert any(
            p.metadata.policy_id == CODING_CERTIFICATION_BEHAVIOR
            for p in default_production_certification_policies(profile="coding")
        )
        coding = CodingProfile.create(odoo_versions=(18,))
        repair = AdapterProfile.create("repair", odoo_versions=(18,))
        coding_cert = {s.stage_id for s in coding.certification_pipeline}
        repair_cert = {s.stage_id for s in repair.certification_pipeline}
        assert CODING_CERTIFICATION_BEHAVIOR in coding_cert
        assert REPAIR_CERTIFICATION_BEHAVIOR in repair_cert
        assert "coding.benchmark.behavior" in {s.stage_id for s in coding.benchmark_pipeline}
        assert CODING_REPORT_BEHAVIOR in {s.stage_id for s in coding.report_pipeline}

    def test_multiple_profiles_structural_only_by_default(self) -> None:
        for profile in ("planner", "conversation", "approval"):
            policies = default_production_certification_policies(profile=profile)
            assert all(
                getattr(
                    p, "criteria", default_structural_certification_criteria()
                ).require_behavior_pass
                is False
                or p.metadata.policy_id.endswith(".behavior")
                for p in policies
            )
            assert not any(
                p.metadata.policy_id.endswith(".certification.behavior") for p in policies
            )


class TestReportOutput:
    def test_report_exposes_criteria_reasons(self) -> None:
        from aiodoo_validation.domain.certification import CertificationExecutionResult
        from aiodoo_validation.domain.report import ReportContext

        policy, context = _cert_context(
            _behavior_score(deferred=True, behavior=None, transform=None, score=0.0)
        )
        cert_result = policy.certify(context)
        assert "behavior_deferred" in cert_result.metadata["criteria_reasons"]

        templates = default_production_report_templates(profile="repair")
        behavior_template = next(
            t for t in templates if t.metadata.template_id == "repair.report.behavior"
        )
        report_context = ReportContext(
            run_id="r1",
            profile_name="repair",
            plan_digest="d",
            protocol_major=1,
            protocol_minor=0,
            execution_tier=ExecutionTier.SMOKE,
            certification_result=cert_result,
            certification_execution=CertificationExecutionResult(
                plan_digest="d",
                profile_name="repair",
                results=(cert_result,),
                duration_ms=1,
                policy_count=1,
                success_count=1,
                failure_count=0,
                certified_count=0,
                overall_certified=False,
            ),
        )
        report = behavior_template.generate(report_context)
        assert report.success is True
        assert report.status == "NOT_CERTIFIED"
        flat = " ".join(" ".join(section.content) for section in report.sections)
        assert "reason=behavior_deferred" in flat
        assert "behavior_deferred" in cert_result.metadata["criteria_reasons"]
