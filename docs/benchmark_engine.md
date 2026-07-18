# Benchmark Engine

**Status:** Production threshold benchmarking active; optional runtime metrics when present

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

## Production behavior

Production policies pass when the source score meets the threshold (100 for
structural oracles). Metadata records real metrics when scoring/oracle results
provide them (`latency_ms`, `tokens_per_sec`, `memory_mb`); otherwise values
remain `None` — never fabricated.

Stub/placeholder policies remain available for `create_with_stubs()` tests only.

## Components

| Component | Responsibility |
|-----------|----------------|
| `BenchmarkEnginePort` | Port: `benchmark(context) → BenchmarkExecutionOutcome` |
| `BenchmarkEngine` | Read plan/profile/score results; run policies |
| `BenchmarkRegistry` | Register / resolve policies by ID |
| `BenchmarkPolicy` protocol | Metadata + `benchmark(BenchmarkContext) → BenchmarkResult` |
| Production policies | Threshold pass + optional runtime metrics |
| Placeholder policies | Stub path / unit tests only |

## Benchmark ID convention (frozen)

Format: `{profile}.benchmark.{name}` — maps 1:1 to `{profile}.score.{name}`

Centralized in `aiodoo_validation.benchmark.ids`. **Do not rename.**
