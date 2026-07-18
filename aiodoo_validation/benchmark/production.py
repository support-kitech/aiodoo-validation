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
from aiodoo_validation.domain.runtime_metrics import RuntimeBenchmarkMetadata

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
    """Pass when score meets the production threshold; capture real metrics only."""

    metadata: BenchmarkMetadata
    threshold: float = _PASS_THRESHOLD

    def benchmark(self, context: BenchmarkContext) -> BenchmarkResult:
        started = perf_counter()
        score = float(context.score_result.score)
        passed = score >= self.threshold
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        score_meta = context.score_result.metadata
        oracle_latency = int(score_meta.get("oracle_duration_ms", 0) or 0)
        runtime = RuntimeBenchmarkMetadata.from_score_metadata(
            score_meta,
            oracle_latency_ms=float(oracle_latency) if oracle_latency else None,
        )
        payload = {
            "placeholder": False,
            "threshold": self.threshold,
            "oracle_latency_ms": oracle_latency,
            "dimensions": score_meta.get("dimensions"),
            "runtime": dict(runtime.as_mapping()),
            # Backward-compatible top-level keys
            "latency_ms": runtime.latency_ms,
            "tokens_per_sec": runtime.tokens_per_sec,
            "memory_mb": runtime.memory_mb,
        }
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
            metadata=MappingProxyType(payload),
        )


def default_production_benchmark_policies(
    *,
    profile: str = "coding",
) -> tuple[ScoreThresholdBenchmarkPolicy, ...]:
    """
    Structural benchmarks for every adapter profile.

    Repair, Coding, and Planner additionally benchmark their behavioral score policies.
    """
    names = ("metadata", "manifest", "python", "xml", "security", "module_structure")
    policies: list[ScoreThresholdBenchmarkPolicy] = [
        ScoreThresholdBenchmarkPolicy(
            metadata=_metadata(
                policy_id=f"{profile}.benchmark.{name}",
                name=f"{name.replace('_', ' ').title()} Benchmark",
                source_score_policy_id=f"{profile}.score.{name}",
                supported_profile=profile,
            )
        )
        for name in names
    ]
    if profile == "repair":
        policies.append(
            ScoreThresholdBenchmarkPolicy(
                metadata=_metadata(
                    policy_id="repair.benchmark.behavior",
                    name="Repair Behavior Benchmark",
                    source_score_policy_id="repair.score.behavior",
                    supported_profile="repair",
                )
            )
        )
    if profile == "coding":
        policies.append(
            ScoreThresholdBenchmarkPolicy(
                metadata=_metadata(
                    policy_id="coding.benchmark.behavior",
                    name="Coding Behavior Benchmark",
                    source_score_policy_id="coding.score.behavior",
                    supported_profile="coding",
                )
            )
        )
    if profile == "planner":
        policies.append(
            ScoreThresholdBenchmarkPolicy(
                metadata=_metadata(
                    policy_id="planner.benchmark.behavior",
                    name="Planner Behavior Benchmark",
                    source_score_policy_id="planner.score.behavior",
                    supported_profile="planner",
                )
            )
        )
    return tuple(policies)


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
