# Scoring Engine

**Status:** Production structural scoring active (primary 100/0); multi-dimension architecture ready

The **Scoring Engine** consumes `OracleExecutionResult` and produces immutable
score results. It never inspects XML, Python, manifests, security files, or
the filesystem. Validation belongs to the Oracle Framework.

Production policies emit dimensional metadata (`structural`, `oracle`,
`behavior`, `weighted`, …) via `scoring.dimensions` while keeping a single
primary `score` for benchmark compatibility. Behavioral dimensions activate
when behavioral oracles are enabled with real corpora.

## Architecture & dependency rule

```text
Correct:
  OracleExecutionResult → ScoringEngine → ScoreExecutionResult

Incorrect:
  ScoringEngine → read XML / Python / filesystem
```

## Production vs stub

| Path | Behavior |
|------|----------|
| `ValidationService.create_default()` / filesystem | Production structural 100/0 + dimensions |
| `create_with_stubs()` | Placeholder policies for CI wiring tests |

`aggregate_score` is the mean of successful policy scores. For production
structural runs this reflects oracle pass/fail rates — not a learned quality
model.

## Score policy ID convention (frozen)

Format: `{profile}.score.{name}` — maps 1:1 to `{profile}.oracle.{name}`

## Explicitly deferred

- Learned / AI grading
- Behavior-weighted aggregates until corpora exist
- Quality score policy (quality oracle disabled)
