# Scoring Engine (Phase 6)

**Status:** Phase 6 — placeholder scoring only (no real formulas)

The **Scoring Engine** consumes `OracleExecutionResult` and produces immutable
score results. It never inspects XML, Python, manifests, security files, or
the filesystem. Validation belongs to the Oracle Framework.

## Architecture & dependency rule

```text
Correct:
  OracleExecutionResult → ScoringEngine → ScoreExecutionResult

Incorrect:
  ScoringEngine → read XML / Python / filesystem
```

```text
Validation Engine
    ↓ OracleRunnerPort
Oracle Framework
    ↓ oracle_execution on RunContext
ScoringEnginePort
    ↓ ScoringEngine → ScoringRegistry → ScorePolicy
ScoreExecutionResult → RunContext.score_execution
```

## Components

| Component | Responsibility |
|-----------|----------------|
| `ScoringEnginePort` | Port: `score(context) → ScoreExecutionOutcome` |
| `ScoringEngine` | Read plan/profile/oracle results; run policies |
| `ScoringRegistry` | Register / resolve policies by ID (plugin-ready) |
| `ScorePolicy` protocol | Metadata + `score(ScoreContext) → ScoreResult` |
| Placeholder policies | Deterministic score `100.0` — no heuristics |

## Score policy ID convention (frozen)

Format: `{profile}.score.{name}` — maps 1:1 to `{profile}.oracle.{name}`

Centralized in `aiodoo_validation.scoring.ids`.

| Policy ID | Source Oracle ID |
|-----------|------------------|
| `coding.score.metadata` | `coding.oracle.metadata` |
| `coding.score.manifest` | `coding.oracle.manifest` |
| `coding.score.python` | `coding.oracle.python` |
| `coding.score.xml` | `coding.oracle.xml` |
| `coding.score.security` | `coding.oracle.security` |
| `coding.score.module_structure` | `coding.oracle.module_structure` |
| `coding.score.quality` | `coding.oracle.quality` (disabled in plan) |

## Lifecycle

1. Require `validation_plan`, `validation_profile`, `oracle_execution`
2. Require `capabilities.supports_scoring`
3. For each **enabled** `scoring_pipeline` stage:
   - Resolve policy from registry
   - Match profile
   - Locate matching `OracleResult` by `source_oracle_id`
   - Invoke policy with `ScoreContext` (oracle result only)
4. Aggregate into `ScoreExecutionResult` (see Placeholder Aggregate below)
5. Attach `score_execution` to `RunContext`

## Placeholder behavior

Every enabled policy returns:

- `score = 100.0` (`PLACEHOLDER_SCORE_VALUE`)
- `success = True`

No weighting, grading, penalties, or ranking.

## Placeholder Aggregate

The `aggregate_score` currently represents the arithmetic mean of successful
placeholder scoring policies.

This is **not** a production scoring algorithm.

It exists only to validate pipeline wiring.

Future phases will replace this placeholder aggregation with the Benchmark
and Certification pipeline.

The aggregate score must not be interpreted as a production quality score.

## RunContext integration

After successful SCORING:

- `score_execution: ScoreExecutionResult`
- Includes per-policy `ScoreResult` values, counts, duration, optional aggregate

Full context after Phase 6:

`artifact_bundle` · `validation_profile` · `validation_plan` · `inference_session`
· `oracle_execution` · `score_execution`

## Error handling

Structured `ScoreError` / `ScoreErrorCode`:

- `missing_oracle_results` / `missing_plan` / `missing_profile`
- `policy_not_found` / `registration_failure`
- `capability_mismatch` / `profile_mismatch`
- `oracle_result_missing` / `execution_failure` / `configuration_failure`

Outcomes return to the Validation Engine; the engine never crashes.

## Future extensibility

- Register real formulas inside policy `score` methods
- Add quality policy when quality oracle is enabled
- New profiles: `{profile}.score.{name}` policies consuming matching oracle IDs

## Explicitly not implemented

No real scoring formulas, grading, weighting, certification, benchmark, reports,
CLI, XML/AST/security/quality analysis, or ecosystem integrations.
