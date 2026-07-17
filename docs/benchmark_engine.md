# Benchmark Engine (Phase 7)

**Status:** Phase 7 — placeholder benchmarking only (no real comparisons)

The **Benchmark Engine** consumes `ScoreExecutionResult` and produces immutable
benchmark results. It never inspects XML, Python, manifests, security files, or
the filesystem. It never re-runs validation or scoring.

## Architecture & dependency rule

```text
Correct:
  ScoreExecutionResult → BenchmarkEngine → BenchmarkExecutionResult

Incorrect:
  BenchmarkEngine → Oracle / XML / Python / filesystem / scoring formulas
```

```text
Validation Engine
    ↓ OracleRunnerPort
Oracle Framework
    ↓ ScoringEnginePort
Scoring Engine
    ↓ score_execution on RunContext
BenchmarkEnginePort
    ↓ BenchmarkEngine → BenchmarkRegistry → BenchmarkPolicy
BenchmarkExecutionResult → RunContext.benchmark_execution
```

## Components

| Component | Responsibility |
|-----------|----------------|
| `BenchmarkEnginePort` | Port: `benchmark(context) → BenchmarkExecutionOutcome` |
| `BenchmarkEngine` | Read plan/profile/score results; run policies |
| `BenchmarkRegistry` | Register / resolve policies by ID (plugin-ready) |
| `BenchmarkPolicy` protocol | Metadata + `benchmark(BenchmarkContext) → BenchmarkResult` |
| Placeholder policies | Deterministic score `100.0`, pass `True`, rank `1` |

## Benchmark ID convention (frozen)

Format: `{profile}.benchmark.{name}` — maps 1:1 to `{profile}.score.{name}`

Centralized in `aiodoo_validation.benchmark.ids`.

| Policy ID | Source Score Policy ID |
|-----------|------------------------|
| `coding.benchmark.metadata` | `coding.score.metadata` |
| `coding.benchmark.manifest` | `coding.score.manifest` |
| `coding.benchmark.python` | `coding.score.python` |
| `coding.benchmark.xml` | `coding.score.xml` |
| `coding.benchmark.security` | `coding.score.security` |
| `coding.benchmark.module_structure` | `coding.score.module_structure` |
| `coding.benchmark.quality` | `coding.score.quality` (disabled in plan) |

## Lifecycle

1. Require `validation_plan`, `validation_profile`, `score_execution`
2. Require `capabilities.supports_benchmark`
3. For each **enabled** `benchmark_pipeline` stage:
   - Resolve policy from registry
   - Match profile
   - Locate matching `ScoreResult` by `source_score_policy_id`
   - Invoke policy with `BenchmarkContext` (score result only)
4. Aggregate into `BenchmarkExecutionResult` (placeholder mean of 100s)
5. Attach `benchmark_execution` to `RunContext`

## Placeholder behavior

Every enabled policy returns:

- `benchmark_score = 100.0`
- `benchmark_pass = True`
- `benchmark_rank = 1`

No dataset comparison, historical analysis, leaderboards, or statistics.

## Placeholder Aggregate

The `aggregate_benchmark_score` is the arithmetic mean of successful placeholder
benchmark scores. It exists only to validate pipeline wiring and must not be
interpreted as a production quality metric.

## RunContext integration

After successful BENCHMARK:

- `benchmark_execution: BenchmarkExecutionResult`

Full context after Phase 7:

`artifact_bundle` · `validation_profile` · `validation_plan` · `inference_session`
· `oracle_execution` · `score_execution` · `benchmark_execution`

## Error handling

Structured `BenchmarkError` / `BenchmarkErrorCode`:

- `missing_score_results` / `missing_plan` / `missing_profile`
- `policy_not_found` / `registration_failure`
- `capability_mismatch` / `profile_mismatch`
- `score_result_missing` / `execution_failure` / `configuration_failure`

## Future extensibility

- Register real comparison logic inside policy `benchmark` methods
- Enable quality benchmark when quality scoring is enabled
- New profiles: `{profile}.benchmark.{name}` consuming matching score IDs

## Explicitly not implemented

No real algorithms, datasets, historical comparison, certification, reports,
CLI, XML/AST/filesystem inspection, validation, scoring, or ecosystem integrations.
