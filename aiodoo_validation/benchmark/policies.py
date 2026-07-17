"""Placeholder benchmark policies (Phase 7 — no real benchmarking)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

from aiodoo_validation.benchmark.ids import (
    CODING_BENCHMARK_MANIFEST,
    CODING_BENCHMARK_METADATA,
    CODING_BENCHMARK_MODULE_STRUCTURE,
    CODING_BENCHMARK_PYTHON,
    CODING_BENCHMARK_QUALITY,
    CODING_BENCHMARK_SECURITY,
    CODING_BENCHMARK_XML,
    PLACEHOLDER_BENCHMARK_PASS,
    PLACEHOLDER_BENCHMARK_RANK,
    PLACEHOLDER_BENCHMARK_SCORE,
)
from aiodoo_validation.domain.benchmark import (
    BenchmarkCapability,
    BenchmarkContext,
    BenchmarkMetadata,
    BenchmarkResult,
)
from aiodoo_validation.scoring.ids import (
    CODING_SCORE_MANIFEST,
    CODING_SCORE_METADATA,
    CODING_SCORE_MODULE_STRUCTURE,
    CODING_SCORE_PYTHON,
    CODING_SCORE_QUALITY,
    CODING_SCORE_SECURITY,
    CODING_SCORE_XML,
)


def placeholder_benchmark_metadata(
    *,
    policy_id: str,
    name: str,
    description: str,
    source_score_policy_id: str,
    supported_profile: str = "coding",
    version: str = "0.0.0-placeholder",
) -> BenchmarkMetadata:
    return BenchmarkMetadata(
        policy_id=policy_id,
        name=name,
        description=description,
        version=version,
        supported_profile=supported_profile,
        source_score_policy_id=source_score_policy_id,
        capabilities=BenchmarkCapability(
            placeholder=True,
            consumes_score_result=True,
            inspects_filesystem=False,
            uses_datasets=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class PlaceholderBenchmarkPolicy:
    """Base placeholder policy returning deterministic benchmark values."""

    metadata: BenchmarkMetadata

    def benchmark(self, context: BenchmarkContext) -> BenchmarkResult:
        started = perf_counter()
        duration_ms = max(0, int((perf_counter() - started) * 1000))
        return BenchmarkResult(
            policy_id=self.metadata.policy_id,
            source_score_policy_id=self.metadata.source_score_policy_id,
            success=True,
            benchmark_score=PLACEHOLDER_BENCHMARK_SCORE,
            benchmark_pass=PLACEHOLDER_BENCHMARK_PASS,
            benchmark_rank=PLACEHOLDER_BENCHMARK_RANK,
            message=(
                f"Placeholder benchmark policy {self.metadata.policy_id!r} "
                f"compared score policy {context.score_result.policy_id!r}."
            ),
            duration_ms=duration_ms,
            metadata=MappingProxyType(
                {
                    "placeholder": True,
                    "score_value": context.score_result.score,
                    "plan_digest": context.plan_digest,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class MetadataBenchmarkPolicy(PlaceholderBenchmarkPolicy):
    @staticmethod
    def create() -> MetadataBenchmarkPolicy:
        return MetadataBenchmarkPolicy(
            metadata=placeholder_benchmark_metadata(
                policy_id=CODING_BENCHMARK_METADATA,
                name="Metadata Benchmark Policy",
                description="Placeholder metadata benchmark policy.",
                source_score_policy_id=CODING_SCORE_METADATA,
            )
        )


@dataclass(frozen=True, slots=True)
class ManifestBenchmarkPolicy(PlaceholderBenchmarkPolicy):
    @staticmethod
    def create() -> ManifestBenchmarkPolicy:
        return ManifestBenchmarkPolicy(
            metadata=placeholder_benchmark_metadata(
                policy_id=CODING_BENCHMARK_MANIFEST,
                name="Manifest Benchmark Policy",
                description="Placeholder manifest benchmark policy.",
                source_score_policy_id=CODING_SCORE_MANIFEST,
            )
        )


@dataclass(frozen=True, slots=True)
class PythonBenchmarkPolicy(PlaceholderBenchmarkPolicy):
    @staticmethod
    def create() -> PythonBenchmarkPolicy:
        return PythonBenchmarkPolicy(
            metadata=placeholder_benchmark_metadata(
                policy_id=CODING_BENCHMARK_PYTHON,
                name="Python Benchmark Policy",
                description="Placeholder Python benchmark policy.",
                source_score_policy_id=CODING_SCORE_PYTHON,
            )
        )


@dataclass(frozen=True, slots=True)
class XmlBenchmarkPolicy(PlaceholderBenchmarkPolicy):
    @staticmethod
    def create() -> XmlBenchmarkPolicy:
        return XmlBenchmarkPolicy(
            metadata=placeholder_benchmark_metadata(
                policy_id=CODING_BENCHMARK_XML,
                name="XML Benchmark Policy",
                description="Placeholder XML benchmark policy.",
                source_score_policy_id=CODING_SCORE_XML,
            )
        )


@dataclass(frozen=True, slots=True)
class SecurityBenchmarkPolicy(PlaceholderBenchmarkPolicy):
    @staticmethod
    def create() -> SecurityBenchmarkPolicy:
        return SecurityBenchmarkPolicy(
            metadata=placeholder_benchmark_metadata(
                policy_id=CODING_BENCHMARK_SECURITY,
                name="Security Benchmark Policy",
                description="Placeholder security benchmark policy.",
                source_score_policy_id=CODING_SCORE_SECURITY,
            )
        )


@dataclass(frozen=True, slots=True)
class ModuleStructureBenchmarkPolicy(PlaceholderBenchmarkPolicy):
    @staticmethod
    def create() -> ModuleStructureBenchmarkPolicy:
        return ModuleStructureBenchmarkPolicy(
            metadata=placeholder_benchmark_metadata(
                policy_id=CODING_BENCHMARK_MODULE_STRUCTURE,
                name="Module Structure Benchmark Policy",
                description="Placeholder module structure benchmark policy.",
                source_score_policy_id=CODING_SCORE_MODULE_STRUCTURE,
            )
        )


@dataclass(frozen=True, slots=True)
class QualityBenchmarkPolicy(PlaceholderBenchmarkPolicy):
    """Future quality benchmark policy (available for plugins; disabled in plan)."""

    @staticmethod
    def create() -> QualityBenchmarkPolicy:
        return QualityBenchmarkPolicy(
            metadata=placeholder_benchmark_metadata(
                policy_id=CODING_BENCHMARK_QUALITY,
                name="Quality Benchmark Policy",
                description="Placeholder future quality benchmark policy.",
                source_score_policy_id=CODING_SCORE_QUALITY,
            )
        )


def default_coding_placeholder_policies() -> tuple[PlaceholderBenchmarkPolicy, ...]:
    return (
        MetadataBenchmarkPolicy.create(),
        ManifestBenchmarkPolicy.create(),
        PythonBenchmarkPolicy.create(),
        XmlBenchmarkPolicy.create(),
        SecurityBenchmarkPolicy.create(),
        ModuleStructureBenchmarkPolicy.create(),
    )
