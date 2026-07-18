# Execution Validation Profile

**Status:** Production execution profile active (structural + behavioral Capability Delivery)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

The **Execution Profile** is a first-class adapter validation profile hosted by
`AdapterProfile` (same host as Repair, Planner, and Conversation). The Execution
**Capability Pack** lives under `capabilities/execution/` and follows the same
Capability Delivery spine as Repair, Coding, Planner, and Conversation.

## Behavior lifecycle

```text
Request metadata
  → evaluation_corpus_id / evaluation_corpus_path
  → AdapterProfile plan builder resolves corpus configuration
  → CapabilityBehavioralOracle (execution)
  → Execution Capability Pack + ExecutionRecordParser
  → ParsedCapabilityRecord → BehaviorCaseBuilder
  → BehaviorRunner
  → BehavioralEvidenceScorePolicy (execution.score.behavior)
  → execution.benchmark.behavior
  → BehaviorGatedCertificationPolicy (execution.certification.behavior)
  → execution.report.behavior
```

Without corpus id/path configuration, the behavior oracle **defers**. Invalid
corpus paths or gate failures produce hard oracle errors.

## Stage IDs

| Stage | ID |
|-------|----|
| Oracle | `execution.oracle.behavior.execution` |
| Score | `execution.score.behavior` |
| Benchmark | `execution.benchmark.behavior` |
| Certification | `execution.certification.behavior` |
| Report | `execution.report.behavior` |

## Corpus

| Item | Value |
|------|-------|
| Builtin pin id | `fixture.execution.eval.behavior` |
| Aliases | `execution.eval`, `execution.eval.fixture` |
| Fixture location | `tests/fixtures/capabilities/execution/eval_corpus/` |
| Request keys | `evaluation_corpus_id`, `evaluation_corpus_path` |

## Public API

`api.build_execution_request` builds an execution `ValidationRequest` (optional
`metadata=` for corpus configuration).

## Components

| Component | Responsibility |
|-----------|----------------|
| `AdapterProfile` | Execution structural + behavior pipelines |
| `capabilities/execution/` | Spec + `ExecutionRecordParser` |
| `CapabilityBehavioralOracle` | Shared behavior oracle (execution registration) |
| `api.build_execution_request` | Public request builder |
