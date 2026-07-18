"""Production certification policies — structural + behavior-gated (E8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.certification.behavioral import BehaviorGatedCertificationPolicy
from aiodoo_validation.certification.criteria import (
    CertificationCriteria,
    default_structural_certification_criteria,
    evaluate_certification_criteria,
)
from aiodoo_validation.domain.certification import (
    CertificationCapability,
    CertificationContext,
    CertificationMetadata,
    CertificationResult,
)
from aiodoo_validation.domain.enums import ValidationKind
from aiodoo_validation.execution import certification_label, is_framework_only_tier


def _metadata(
    *,
    policy_id: str,
    name: str,
    source_benchmark_policy_id: str,
    supported_profile: str,
) -> CertificationMetadata:
    return CertificationMetadata(
        policy_id=policy_id,
        name=name,
        description=f"Production certification for {source_benchmark_policy_id}.",
        version="1.0.0",
        supported_profile=supported_profile,
        source_benchmark_policy_id=source_benchmark_policy_id,
        capabilities=CertificationCapability(
            placeholder=False,
            consumes_benchmark_result=True,
            inspects_filesystem=False,
            applies_thresholds=True,
        ),
    )


@dataclass(frozen=True, slots=True)
class BenchmarkPassCertificationPolicy:
    """
    Certify using reusable CertificationCriteria from structural benchmarks.

    Behavior gates are owned by ``BehaviorGatedCertificationPolicy`` when a
    profile registers one — this policy stays structural/benchmark-oriented.
    """

    metadata: CertificationMetadata
    criteria: CertificationCriteria = field(
        default_factory=default_structural_certification_criteria
    )

    def certify(self, context: CertificationContext) -> CertificationResult:
        started = perf_counter()
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        bench = context.benchmark_result
        score_meta = bench.metadata
        dimensions: dict = {}
        raw_dimensions = score_meta.get("dimensions")
        if isinstance(raw_dimensions, dict):
            dimensions = raw_dimensions

        evaluation = evaluate_certification_criteria(
            self.criteria,
            execution_tier=context.execution_tier,
            structural_pass=bool(bench.benchmark_pass),
            behavior_pass=None,
            behavior_deferred=False,
            benchmark_pass=bool(bench.benchmark_pass),
            oracle_score=float(bench.benchmark_score),
            behavior_score=None,
            weighted_score=(
                float(dimensions["weighted"])
                if dimensions.get("weighted") is not None
                else float(bench.benchmark_score)
            ),
            benchmark_score=float(bench.benchmark_score),
            validation_kind=ValidationKind.STRUCTURAL,
        )

        label = certification_label(
            profile_name=context.profile_name,
            certified=evaluation.certified,
        )
        if is_framework_only_tier(context.execution_tier):
            message = "Standard tier never production-certifies."
        elif evaluation.certified:
            message = f"Certification granted ({label})."
        else:
            message = (
                f"Certification denied ({label}): "
                + ", ".join(evaluation.reasons)
            )

        return CertificationResult(
            policy_id=self.metadata.policy_id,
            source_benchmark_policy_id=self.metadata.source_benchmark_policy_id,
            success=True,
            certified=evaluation.certified,
            certification_score=(
                float(bench.benchmark_score) if evaluation.certified else 0.0
            ),
            certification_level="PASS" if evaluation.certified else "NOT_CERTIFIED",
            message=message,
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "framework_only": is_framework_only_tier(context.execution_tier),
                    "certification_label": label,
                    "criteria_reasons": evaluation.reasons,
                    "criteria_signals": dict(evaluation.signals),
                    "validation_kind": ValidationKind.STRUCTURAL.value,
                    "benchmark_pass": bool(bench.benchmark_pass),
                    "benchmark_score": float(bench.benchmark_score),
                }
            ),
        )


def default_production_certification_policies(
    *,
    profile: str = "coding",
) -> tuple[BenchmarkPassCertificationPolicy | BehaviorGatedCertificationPolicy, ...]:
    """
    Structural certification for every adapter profile.

    Repair additionally registers the E8 behavior-gated policy. Registration
    stays here so ``production.py`` need not change.
    """
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    criteria = default_structural_certification_criteria()
    policies: list[BenchmarkPassCertificationPolicy | BehaviorGatedCertificationPolicy] = [
        BenchmarkPassCertificationPolicy(
            metadata=_metadata(
                policy_id=f"{profile}.certification.{name}",
                name=f"{name.replace('_', ' ').title()} Certification",
                source_benchmark_policy_id=f"{profile}.benchmark.{name}",
                supported_profile=profile,
            ),
            criteria=criteria,
        )
        for name in names
    ]
    if profile == "repair":
        policies.append(BehaviorGatedCertificationPolicy.create_for_repair())
    return tuple(policies)


def default_production_coding_certification_policies(
    *,
    supported_profile: str = "coding",
) -> tuple[BenchmarkPassCertificationPolicy | BehaviorGatedCertificationPolicy, ...]:
    return default_production_certification_policies(profile=supported_profile)


__all__ = [
    "BehaviorGatedCertificationPolicy",
    "BenchmarkPassCertificationPolicy",
    "default_production_certification_policies",
    "default_production_coding_certification_policies",
]
