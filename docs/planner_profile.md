# Planner Validation Profile

**Status:** Production planner profile active (structural + behavioral Capability Delivery)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

The **Planner Profile** is a first-class adapter validation profile hosted by
`AdapterProfile` (same host as Repair). The Planner **Capability Pack** lives
under `capabilities/planner/` and follows the same Capability Delivery spine as
Repair and Coding.

## Behavior lifecycle

```text
Request metadata
  → evaluation_corpus_id / evaluation_corpus_path
  → AdapterProfile plan builder resolves corpus configuration
  → CapabilityBehavioralOracle (planner)
  → Planner Capability Pack + PlannerRecordParser
  → ParsedCapabilityRecord → BehaviorCaseBuilder
  → BehaviorRunner
  → BehavioralEvidenceScorePolicy (planner.score.behavior)
  → planner.benchmark.behavior
  → BehaviorGatedCertificationPolicy (planner.certification.behavior)
  → planner.report.behavior
```

Without corpus id/path configuration, the behavior oracle **defers**. Invalid
corpus paths or gate failures produce hard oracle errors.

## Stage IDs

| Stage | ID |
|-------|----|
| Oracle | `planner.oracle.behavior.planner` |
| Score | `planner.score.behavior` |
| Benchmark | `planner.benchmark.behavior` |
| Certification | `planner.certification.behavior` |
| Report | `planner.report.behavior` |

## Corpus

| Item | Value |
|------|-------|
| Builtin pin id | `fixture.planner.eval.behavior` |
| Aliases | `planner.eval`, `planner.eval.fixture` |
| Fixture location | `tests/fixtures/capabilities/planner/eval_corpus/` |
| Request keys | `evaluation_corpus_id`, `evaluation_corpus_path` |

## Public API

`api.build_planner_request` builds a planner `ValidationRequest` (optional
`metadata=` for corpus configuration).

## Components

| Component | Responsibility |
|-----------|----------------|
| `AdapterProfile` | Planner structural + behavior pipelines |
| `capabilities/planner/` | Spec + `PlannerRecordParser` |
| `CapabilityBehavioralOracle` | Shared behavior oracle (planner registration) |
| `api.build_planner_request` | Public request builder |
