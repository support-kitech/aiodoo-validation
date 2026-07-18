"""Unit tests for post-freeze extensibility refinements."""

from __future__ import annotations

from types import MappingProxyType

from aiodoo_validation.comparators import ComparatorRegistry, ExactMatchComparator
from aiodoo_validation.domain.context import RunContext
from aiodoo_validation.domain.enums import BehaviorStatus, ComparatorKind, ExecutionTier
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.runtime_metrics import RuntimeBenchmarkMetadata
from aiodoo_validation.execution import (
    certification_label,
    certification_label_kind,
    certification_label_versioned,
)
from aiodoo_validation.reporting.engine import _build_run_summary


def test_runtime_benchmark_metadata_serializes_optional_schema() -> None:
    empty = RuntimeBenchmarkMetadata()
    mapping = dict(empty.as_mapping())
    assert mapping["latency_ms"] is None
    assert mapping["prompt_tokens"] is None
    assert mapping["peak_gpu_memory_mb"] is None
    assert mapping["cache_hit"] is None
    assert "throughput_tokens_per_second" in mapping
    assert "context_window" in mapping

    populated = RuntimeBenchmarkMetadata.from_score_metadata(
        MappingProxyType(
            {
                "latency_ms": 12.5,
                "tokens_per_sec": 40.0,
                "memory_mb": 256.0,
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            }
        )
    )
    assert populated.latency_ms == 12.5
    assert populated.tokens_per_sec == 40.0
    assert populated.throughput_tokens_per_second == 40.0
    assert populated.peak_cpu_memory_mb == 256.0
    assert populated.prompt_tokens == 10
    assert populated.generation_time_ms is None
    assert populated.peak_gpu_memory_mb is None


def test_runtime_metadata_never_fabricates_from_empty() -> None:
    runtime = RuntimeBenchmarkMetadata.from_score_metadata({})
    assert all(value is None for value in runtime.as_mapping().values())


def test_certification_label_helpers_are_backward_compatible() -> None:
    assert certification_label(profile_name="coding", certified=True) == "coding-certified"
    assert certification_label(profile_name="coding", certified=False) == "coding-not-certified"
    assert (
        certification_label_versioned(profile_name="planner", certified=True)
        == "planner-certified-v1"
    )
    assert (
        certification_label_kind(profile_name="repair", certified=True)
        == "repair-certified-structural"
    )
    assert (
        certification_label_kind(
            profile_name="conversation",
            certified=False,
            kind="structural",
        )
        == "conversation-not-certified-structural"
    )


def test_comparator_capability_metadata_is_descriptive() -> None:
    caps = ExactMatchComparator().metadata.capabilities
    assert caps.implemented is True
    assert caps.deterministic is True
    assert caps.supports_cpu is True
    assert caps.requires_model is False
    mapping = caps.as_mapping()
    assert "supports_batch" in mapping
    assert "behavioral_only" in mapping
    assert "placeholder" in mapping

    deferred = ComparatorRegistry.create_default().get(ComparatorKind.SEMANTIC)
    assert deferred.metadata.capabilities.placeholder is True
    assert deferred.metadata.capabilities.requires_model is True
    assert deferred.metadata.capabilities.implemented is False


def test_behavior_status_enum_values() -> None:
    assert BehaviorStatus.DEFERRED.value == "deferred"
    assert BehaviorStatus.ACTIVE.value == "active"
    assert {status.value for status in BehaviorStatus} >= {
        "not_available",
        "deferred",
        "disabled",
        "skipped",
        "active",
        "passed",
        "failed",
        "unknown",
    }


def test_run_summary_convenience_fields_without_filesystem() -> None:
    context = RunContext.begin(
        ValidationRequest(
            profile_name="coding",
            base_model_ref="base",
            adapter_ref="adapter",
            execution_tier=ExecutionTier.STANDARD,
        )
    )
    summary = _build_run_summary(context)
    assert summary["behavior_status"] == BehaviorStatus.DEFERRED.value
    assert summary["behavior_validation"]["status"] == BehaviorStatus.DEFERRED.value
    assert summary["validation_kind"] == "structural"
    assert summary["execution_mode"] == "framework"
    assert summary["report_version"] == "1.1.0"
    assert summary["protocol_version"] == "1.0"
    assert summary["repository_version"]
    assert summary["certification_label"] == "coding-not-certified"
    assert summary["overall_certified"] is None
    assert summary["overall_status"] == "unknown"
    assert "artifacts" in summary
