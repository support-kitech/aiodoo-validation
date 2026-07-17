# Certification Engine (Phase 8)

**Status:** Phase 8 — placeholder certification only (no production rules)

The **Certification Engine** consumes `BenchmarkExecutionResult` and produces
immutable certification results. It never inspects XML, Python, manifests,
security files, or the filesystem. It never re-runs validation, scoring, or
benchmarking.

## Architecture & dependency rule

```text
Correct:
  BenchmarkExecutionResult → CertificationEngine → CertificationExecutionResult

Incorrect:
  CertificationEngine → Oracle / Scoring / Benchmark execution / XML / filesystem
```

```text
Validation Engine
    ↓ OracleRunnerPort
Oracle Framework
    ↓ ScoringEnginePort
Scoring Engine
    ↓ BenchmarkEnginePort
Benchmark Engine
    ↓ benchmark_execution on RunContext
CertificationEnginePort
    ↓ CertificationEngine → CertificationRegistry → CertificationPolicy
CertificationExecutionResult → RunContext.certification_execution
```

## Components

| Component | Responsibility |
|-----------|----------------|
| `CertificationEnginePort` | Port: `certify(context) → CertificationExecutionOutcome` |
| `CertificationEngine` | Read plan/profile/benchmark results; run policies |
| `CertificationRegistry` | Register / resolve policies by ID (plugin-ready) |
| `CertificationPolicy` protocol | Metadata + `certify(CertificationContext) → CertificationResult` |
| Placeholder policies | `certified=True`, score `100.0`, level `"PASS"` |

## Certification ID convention (frozen)

Format: `{profile}.certification.{name}` — maps 1:1 to `{profile}.benchmark.{name}`

Centralized in `aiodoo_validation.certification.ids`.

**These IDs are frozen and must never be renamed.**

| Policy ID | Source Benchmark Policy ID |
|-----------|----------------------------|
| `coding.certification.metadata` | `coding.benchmark.metadata` |
| `coding.certification.manifest` | `coding.benchmark.manifest` |
| `coding.certification.python` | `coding.benchmark.python` |
| `coding.certification.xml` | `coding.benchmark.xml` |
| `coding.certification.security` | `coding.benchmark.security` |
| `coding.certification.module_structure` | `coding.benchmark.module_structure` |
| `coding.certification.quality` | `coding.benchmark.quality` (disabled in plan) |

## What Certification does NOT do

Certification **never**:

- validates artifacts or runs oracles
- scores findings
- benchmarks scores
- parses XML / Python / manifests
- inspects the filesystem
- applies production thresholds or grading

Certification **only** consumes `BenchmarkExecutionResult` / `BenchmarkResult`.

## Lifecycle

1. Require `validation_plan`, `validation_profile`, `benchmark_execution`
2. Require `capabilities.supports_certification`
3. For each **enabled** `certification_pipeline` stage:
   - Resolve policy from registry
   - Match profile
   - Locate matching `BenchmarkResult` by `source_benchmark_policy_id`
   - Invoke policy with `CertificationContext` (benchmark result only)
4. Aggregate into `CertificationExecutionResult`
5. Attach `certification_execution` to `RunContext`

## Placeholder behavior

Every enabled policy returns:

- `certified = True`
- `certification_score = 100.0`
- `certification_level = "PASS"`

No thresholds, grading, AI decisions, or production policy evaluation.

## Placeholder Aggregate

The `aggregate_certification_score` is the arithmetic mean of successful
placeholder certification scores. `overall_certified` is true when all enabled
policies succeed and certify.

**`overall_certified` and `aggregate_certification_score` are NOT production
certification decisions.** The placeholder values exist only to validate pipeline
wiring. Future certification policies will replace these placeholder values. They
must never be interpreted as production certification decisions.

## RunContext integration

After successful CERTIFICATION:

- `certification_execution: CertificationExecutionResult`

Full context after Phase 8:

`artifact_bundle` · `validation_profile` · `validation_plan` · `inference_session`
· `oracle_execution` · `score_execution` · `benchmark_execution`
· `certification_execution`

## Error handling

Structured `CertificationError` / `CertificationErrorCode`:

- `missing_benchmark_results` / `missing_plan` / `missing_profile`
- `policy_not_found` / `registration_failure`
- `capability_mismatch` / `profile_mismatch`
- `benchmark_result_missing` / `execution_failure` / `configuration_failure`

## Future extensibility

- Register real certification rules inside policy `certify` methods
- Enable quality certification when quality benchmarking is enabled
- New profiles: `{profile}.certification.{name}` consuming matching benchmark IDs

## Explicitly not implemented

No production certification, thresholds, grading, reports, CLI, XML/AST/filesystem
inspection, validation, scoring, benchmarking, or ecosystem integrations.
