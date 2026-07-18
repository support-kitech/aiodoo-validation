# Evaluation Validation Profile

**Status:** Production evaluation profile active (structural + behavioral Capability Delivery)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

The **Evaluation Profile** is a first-class adapter validation profile hosted by
`AdapterProfile`. The Evaluation **Capability Pack** lives under
`capabilities/evaluation/` and follows the same Capability Delivery spine as
Repair, Coding, Planner, Conversation, Execution, and Approval.

## Behavior lifecycle

```text
Request metadata
  → evaluation_corpus_id / evaluation_corpus_path
  → AdapterProfile plan builder resolves corpus configuration
  → CapabilityBehavioralOracle (evaluation)
  → Evaluation Capability Pack + EvaluationRecordParser
  → ParsedCapabilityRecord → BehaviorCaseBuilder
  → BehaviorRunner
  → BehavioralEvidenceScorePolicy (evaluation.score.behavior)
  → evaluation.benchmark.behavior
  → BehaviorGatedCertificationPolicy (evaluation.certification.behavior)
  → evaluation.report.behavior
```

Without corpus id/path configuration, the behavior oracle **defers**. Invalid
corpus paths or gate failures produce hard oracle errors.

## Stage IDs

| Stage | ID |
|-------|----|
| Oracle | `evaluation.oracle.behavior.evaluation` |
| Score | `evaluation.score.behavior` |
| Benchmark | `evaluation.benchmark.behavior` |
| Certification | `evaluation.certification.behavior` |
| Report | `evaluation.report.behavior` |

## Corpus

| Item | Value |
|------|-------|
| Builtin pin id | `fixture.evaluation.eval.behavior` |
| Aliases | `evaluation.eval`, `evaluation.eval.fixture` |
| Fixture location | `tests/fixtures/capabilities/evaluation/eval_corpus/` |
| Request keys | `evaluation_corpus_id`, `evaluation_corpus_path` |

## Public API

`api.build_evaluation_request` builds an evaluation `ValidationRequest` (optional
`metadata=` for corpus configuration).

## Components

| Component | Responsibility |
|-----------|----------------|
| `AdapterProfile` | Evaluation structural + behavior pipelines |
| `capabilities/evaluation/` | Spec + `EvaluationRecordParser` |
| `CapabilityBehavioralOracle` | Shared behavior oracle (evaluation registration) |
| `api.build_evaluation_request` | Public request builder |
