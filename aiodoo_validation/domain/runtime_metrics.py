"""Optional runtime benchmark metadata schema for future inference runtimes.

All fields are optional. Values must be provided by the runtime when known;
never estimate or invent metrics.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any


def _optional_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _optional_int(value: object) -> int | None:
    number = _optional_number(value)
    if number is None:
        return None
    return int(number)


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return None


@dataclass(frozen=True, slots=True)
class RuntimeBenchmarkMetadata:
    """
    Extensible runtime metrics attached to benchmark results.

    Existing consumers may read ``latency_ms``, ``tokens_per_sec``, and
    ``memory_mb``. Additional fields are reserved for future runtimes.
    """

    latency_ms: float | None = None
    tokens_per_sec: float | None = None
    memory_mb: float | None = None
    generation_time_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    peak_gpu_memory_mb: float | None = None
    peak_cpu_memory_mb: float | None = None
    gpu_utilization_percent: float | None = None
    cpu_utilization_percent: float | None = None
    throughput_tokens_per_second: float | None = None
    model_load_time_ms: float | None = None
    warmup_time_ms: float | None = None
    cache_hit: bool | None = None
    cache_miss: bool | None = None
    batch_size: int | None = None
    context_window: int | None = None

    def as_mapping(self) -> Mapping[str, Any]:
        """Serialize all schema keys (including ``None`` values)."""
        return MappingProxyType(dict(asdict(self)))

    @classmethod
    def from_score_metadata(
        cls,
        score_meta: Mapping[str, Any],
        *,
        oracle_latency_ms: float | None = None,
    ) -> RuntimeBenchmarkMetadata:
        """Build metadata from score/oracle signals without inventing values."""
        latency = _optional_number(score_meta.get("latency_ms"))
        if latency is None and oracle_latency_ms is not None:
            latency = float(oracle_latency_ms)
        tokens_per_sec = _optional_number(score_meta.get("tokens_per_sec"))
        throughput = _optional_number(score_meta.get("throughput_tokens_per_second"))
        if throughput is None:
            throughput = tokens_per_sec
        memory = _optional_number(score_meta.get("memory_mb"))
        peak_cpu = _optional_number(score_meta.get("peak_cpu_memory_mb"))
        if peak_cpu is None:
            peak_cpu = memory
        return cls(
            latency_ms=latency,
            tokens_per_sec=tokens_per_sec,
            memory_mb=memory,
            generation_time_ms=_optional_number(score_meta.get("generation_time_ms")),
            prompt_tokens=_optional_int(score_meta.get("prompt_tokens")),
            completion_tokens=_optional_int(score_meta.get("completion_tokens")),
            total_tokens=_optional_int(score_meta.get("total_tokens")),
            peak_gpu_memory_mb=_optional_number(score_meta.get("peak_gpu_memory_mb")),
            peak_cpu_memory_mb=peak_cpu,
            gpu_utilization_percent=_optional_number(score_meta.get("gpu_utilization_percent")),
            cpu_utilization_percent=_optional_number(score_meta.get("cpu_utilization_percent")),
            throughput_tokens_per_second=throughput,
            model_load_time_ms=_optional_number(score_meta.get("model_load_time_ms")),
            warmup_time_ms=_optional_number(score_meta.get("warmup_time_ms")),
            cache_hit=_optional_bool(score_meta.get("cache_hit")),
            cache_miss=_optional_bool(score_meta.get("cache_miss")),
            batch_size=_optional_int(score_meta.get("batch_size")),
            context_window=_optional_int(score_meta.get("context_window")),
        )


__all__ = ["RuntimeBenchmarkMetadata"]
