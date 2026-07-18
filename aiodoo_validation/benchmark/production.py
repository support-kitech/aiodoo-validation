"""Production benchmark policies — compare scores and record runtime signals."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.domain.benchmark import (
    BenchmarkCapability,
    BenchmarkContext,
    BenchmarkMetadata,
    BenchmarkResult,
)

_PASS_THRESHOLD = 100.0


def _metadata(
    *,
    policy_id: str,
    name: str,
    source_score_policy_id: str,
    supported_profile: str,
) -> BenchmarkMetadata:
    return BenchmarkMetadata(
        policy_id=policy_id,
        name=name,
        description=f"Production benchmark for {source_score_policy_id}.",
        version="1.0.0",
        supported_profile=supported_profile,
        source_score_policy_id=source_score_policy_id,
        capabilities=BenchmarkCapability(
            placeholder=False,
            consumes_score_result=True,
            inspects_filesystem=False,
            uses_datasets=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class ScoreThresholdBenchmarkPolicy:
    """Pass when score meets the production threshold; capture latency metadata."""

    metadata: BenchmarkMetadata
    threshold: float = _PASS_THRESHOLD

    def benchmark(self, context: BenchmarkContext) -> BenchmarkResult:
        started = perf_counter()
        score = float(context.score_result.score)
        passed = score >= self.threshold
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        oracle_latency = int(context.score_result.metadata.get("oracle_duration_ms", 0) or 0)
        return BenchmarkResult(
            policy_id=self.metadata.policy_id,
            source_score_policy_id=self.metadata.source_score_policy_id,
            success=True,
            benchmark_score=score,
            benchmark_pass=passed,
            benchmark_rank=1 if passed else 2,
            message=(
                f"Benchmark {'PASS' if passed else 'FAIL'} "
                f"(score={score:.1f}, threshold={self.threshold:.1f})."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": False,
                    "threshold": self.threshold,
                    "oracle_latency_ms": oracle_latency,
                    "tokens_per_sec": None,
                    "memory_mb": None,
                }
            ),
        )


def default_production_benchmark_policies(
    *,
    profile: str = "coding",
) -> tuple[ScoreThresholdBenchmarkPolicy, ...]:
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    return tuple(
        ScoreThresholdBenchmarkPolicy(
            metadata=_metadata(
                policy_id=f"{profile}.benchmark.{name}",
                name=f"{name.replace('_', ' ').title()} Benchmark",
                source_score_policy_id=f"{profile}.score.{name}",
                supported_profile=profile,
            )
        )
        for name in names
    )


def default_production_coding_benchmark_policies(
    *,
    supported_profile: str = "coding",
) -> tuple[ScoreThresholdBenchmarkPolicy, ...]:
    return default_production_benchmark_policies(profile=supported_profile)


__all__ = [
    "ScoreThresholdBenchmarkPolicy",
    "default_production_benchmark_policies",
    "default_production_coding_benchmark_policies",
]
