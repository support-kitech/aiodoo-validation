# Post-Freeze Extensibility Refinements

**Status:** Implemented — descriptive / optional schema only; Protocol V1 unchanged

This document describes future-ready metadata added after the Protocol V1 freeze.
None of these changes alter CLI output, public API contracts, or pipeline order.

## Implemented vs future-ready

| Capability | Status |
|------------|--------|
| Runtime benchmark metadata schema | **Implemented** (optional fields; mostly `None` today) |
| Version/kind certification label helpers | **Implemented** (CLI still uses stable `certification_label()`) |
| Run summary convenience fields | **Implemented** |
| Comparator capability metadata | **Implemented** (descriptive only) |
| `BehaviorStatus` enum | **Implemented** (production reports `deferred`) |
| Populating GPU/cache/batch metrics | **Future-ready** — when runtimes provide values |
| CLI using versioned labels | **Future-ready** — intentionally not switched |
| Behavioral evaluation | **Deferred** — no corpora |

## Runtime benchmark metadata

`RuntimeBenchmarkMetadata` (`domain/runtime_metrics.py`) defines optional fields:

`latency_ms`, `tokens_per_sec`, `memory_mb`, `generation_time_ms`,
`prompt_tokens`, `completion_tokens`, `total_tokens`, `peak_gpu_memory_mb`,
`peak_cpu_memory_mb`, `gpu_utilization_percent`, `cpu_utilization_percent`,
`throughput_tokens_per_second`, `model_load_time_ms`, `warmup_time_ms`,
`cache_hit`, `cache_miss`, `batch_size`, `context_window`

Production benchmarks nest the full schema under `metadata["runtime"]` and keep
legacy top-level `latency_ms` / `tokens_per_sec` / `memory_mb` keys for
compatibility. Missing values are `None` — never estimated.

## Certification labels

| Helper | Example | Used by CLI today |
|--------|---------|-------------------|
| `certification_label()` | `coding-certified` | **Yes** |
| `certification_label_versioned()` | `coding-certified-v1` | No |
| `certification_label_kind()` | `coding-certified-structural` | No |

## Run summary convenience fields

Top-level keys added alongside existing nested blocks:

`overall_status`, `overall_score`, `overall_certified`, `validation_kind`,
`report_version`, `protocol_version`, `profile_version`, `execution_mode`,
`behavior_status`, `certification_label`, `repository_version`

## Comparator capabilities

`ComparatorCapability` declares requirements and execution traits
(`requires_*`, `supports_*`, `deterministic`, `behavioral_only`, `placeholder`, …).
Execution paths ignore these flags today.

## Behavior status

`BehaviorStatus` enum replaces free-form strings. Without a behavioral corpus,
production summaries use `BehaviorStatus.DEFERRED` (`"deferred"`).
