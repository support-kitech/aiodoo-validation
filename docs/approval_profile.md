# Approval Validation Profile

**Status:** Production approval profile active (structural + behavioral Capability Delivery)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

The **Approval Profile** is a first-class adapter validation profile hosted by
`AdapterProfile`. The Approval **Capability Pack** lives under
`capabilities/approval/` and follows the same Capability Delivery spine as
Repair, Coding, Planner, Conversation, Execution, and Evaluation.

## Behavior lifecycle

```text
Request metadata
  → evaluation_corpus_id / evaluation_corpus_path
  → AdapterProfile plan builder resolves corpus configuration
  → CapabilityBehavioralOracle (approval)
  → Approval Capability Pack + ApprovalRecordParser
  → ParsedCapabilityRecord → BehaviorCaseBuilder
  → BehaviorRunner
  → BehavioralEvidenceScorePolicy (approval.score.behavior)
  → approval.benchmark.behavior
  → BehaviorGatedCertificationPolicy (approval.certification.behavior)
  → approval.report.behavior
```

Without corpus id/path configuration, the behavior oracle **defers**. Invalid
corpus paths or gate failures produce hard oracle errors.

## Stage IDs

| Stage | ID |
|-------|----|
| Oracle | `approval.oracle.behavior.approval` |
| Score | `approval.score.behavior` |
| Benchmark | `approval.benchmark.behavior` |
| Certification | `approval.certification.behavior` |
| Report | `approval.report.behavior` |

## Corpus

| Item | Value |
|------|-------|
| Builtin pin id | `fixture.approval.eval.behavior` |
| Aliases | `approval.eval`, `approval.eval.fixture` |
| Fixture location | `tests/fixtures/capabilities/approval/eval_corpus/` |
| Request keys | `evaluation_corpus_id`, `evaluation_corpus_path` |

## Public API

`api.build_approval_request` builds an approval `ValidationRequest` (optional
`metadata=` for corpus configuration).

## Components

| Component | Responsibility |
|-----------|----------------|
| `AdapterProfile` | Approval structural + behavior pipelines |
| `capabilities/approval/` | Spec + `ApprovalRecordParser` |
| `CapabilityBehavioralOracle` | Shared behavior oracle (approval registration) |
| `api.build_approval_request` | Public request builder |
