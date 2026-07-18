# Certification Engine

**Status:** Production structural certification active; reusable criteria architecture ready

The **Certification Engine** consumes `BenchmarkExecutionResult` and produces
immutable certification results. It never inspects XML, Python, manifests,
security files, or the filesystem. It never re-runs validation, scoring, or
benchmarking.

Production policies use `certification.criteria` (`CertificationCriteria` /
`evaluate_certification_criteria`) so future behavior gates and profile
thresholds can be enabled without redesign. Today `require_behavior_pass`
defaults to **False** — certification is structural/benchmark based.
Standard tier never certifies. Labels are profile-driven (`coding-certified`).

## Architecture & dependency rule

```text
Correct:
  BenchmarkExecutionResult → CertificationEngine → CertificationExecutionResult

Incorrect:
  CertificationEngine → Oracle / Scoring / Benchmark execution / XML / filesystem
```

## Production vs stub

| Path | Behavior |
|------|----------|
| Filesystem / CLI default | Criteria + benchmark pass; profile labels |
| Stub path | Placeholder policies for wiring tests only |

`overall_certified` is true when all enabled production policies succeed and
certify. On `standard` tier, policies intentionally deny certification.

## Explicitly deferred

- Behavior-gated certification until evaluation corpora exist
- Profile-specific threshold packs beyond structural defaults
- Quality certification (quality pipeline stage disabled)
