"""Production certification policies — certify from benchmark outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.certification import (
    CertificationCapability,
    CertificationContext,
    CertificationMetadata,
    CertificationResult,
)
from aiodoo_validation.execution import is_framework_only_tier


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
    """Certify when the source benchmark passed; never on standard tier."""

    metadata: CertificationMetadata

    def certify(self, context: CertificationContext) -> CertificationResult:
        started = perf_counter()
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        if is_framework_only_tier(context.execution_tier):
            return CertificationResult(
                policy_id=self.metadata.policy_id,
                source_benchmark_policy_id=self.metadata.source_benchmark_policy_id,
                success=True,
                certified=False,
                certification_score=0.0,
                certification_level="NOT_CERTIFIED",
                message="Standard tier never production-certifies.",
                duration_ms=duration_ms,
                metadata=MappingProxyType(
                    {"placeholder": False, "framework_only": True}
                ),
            )

        passed = bool(context.benchmark_result.benchmark_pass)
        score = float(context.benchmark_result.benchmark_score)
        return CertificationResult(
            policy_id=self.metadata.policy_id,
            source_benchmark_policy_id=self.metadata.source_benchmark_policy_id,
            success=True,
            certified=passed,
            certification_score=score if passed else 0.0,
            certification_level="PASS" if passed else "FAIL",
            message=(
                f"Certification {'granted' if passed else 'denied'} "
                f"for benchmark {context.benchmark_result.policy_id!r}."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "benchmark_pass": passed,
                    "benchmark_score": score,
                }
            ),
        )


def default_production_certification_policies(
    *,
    profile: str = "coding",
) -> tuple[BenchmarkPassCertificationPolicy, ...]:
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    return tuple(
        BenchmarkPassCertificationPolicy(
            metadata=_metadata(
                policy_id=f"{profile}.certification.{name}",
                name=f"{name.replace('_', ' ').title()} Certification",
                source_benchmark_policy_id=f"{profile}.benchmark.{name}",
                supported_profile=profile,
            )
        )
        for name in names
    )


def default_production_coding_certification_policies(
    *,
    supported_profile: str = "coding",
) -> tuple[BenchmarkPassCertificationPolicy, ...]:
    return default_production_certification_policies(profile=supported_profile)


__all__ = [
    "BenchmarkPassCertificationPolicy",
    "default_production_certification_policies",
    "default_production_coding_certification_policies",
]
