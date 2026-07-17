"""Benchmark Engine package (Phase 7)."""

from aiodoo_validation.benchmark.base import BenchmarkPolicy
from aiodoo_validation.benchmark.engine import BenchmarkEngine
from aiodoo_validation.benchmark.policies import (
    ManifestBenchmarkPolicy,
    MetadataBenchmarkPolicy,
    ModuleStructureBenchmarkPolicy,
    PlaceholderBenchmarkPolicy,
    PythonBenchmarkPolicy,
    QualityBenchmarkPolicy,
    SecurityBenchmarkPolicy,
    XmlBenchmarkPolicy,
)
from aiodoo_validation.benchmark.registry import BenchmarkRegistry

__all__ = [
    "BenchmarkEngine",
    "BenchmarkPolicy",
    "BenchmarkRegistry",
    "ManifestBenchmarkPolicy",
    "MetadataBenchmarkPolicy",
    "ModuleStructureBenchmarkPolicy",
    "PlaceholderBenchmarkPolicy",
    "PythonBenchmarkPolicy",
    "QualityBenchmarkPolicy",
    "SecurityBenchmarkPolicy",
    "XmlBenchmarkPolicy",
]
