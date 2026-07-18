# Repair Validation Profile

**Status:** Production repair profile active (structural + behavioral Capability Delivery)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

The **Repair Profile** is a first-class adapter validation profile hosted by
`AdapterProfile`. The Repair **Capability Pack** lives under
`capabilities/repair/` and follows the same Capability Delivery spine as Coding,
Planner, Conversation, Execution, Approval, and Evaluation.

## Behavior lifecycle

```text
Request metadata
  → evaluation_corpus_id / evaluation_corpus_path
  → AdapterProfile plan builder resolves corpus configuration
  → CapabilityBehavioralOracle (repair)
  → Repair Capability Pack + RepairRecordParser
  → ParsedCapabilityRecord → BehaviorCaseBuilder
  → BehaviorRunner
  → BehavioralEvidenceScorePolicy (repair.score.behavior)
  → repair.benchmark.behavior
  → BehaviorGatedCertificationPolicy (repair.certification.behavior)
  → repair.report.behavior
```

Without corpus id/path configuration, the behavior oracle **defers**. Invalid
corpus paths or gate failures produce hard oracle errors.

## Stage IDs

| Stage | ID |
|-------|----|
| Oracle | `repair.oracle.behavior.repair` |
| Score | `repair.score.behavior` |
| Benchmark | `repair.benchmark.behavior` |
| Certification | `repair.certification.behavior` |
| Report | `repair.report.behavior` |

## Corpus

| Item | Value |
|------|-------|
| Builtin pin id | `fixture.repair.eval.behavior` |
| Aliases | `repair.eval`, `repair.eval.fixture` |
| Fixture location | `tests/fixtures/capabilities/repair/eval_corpus/` |
| Request keys | `evaluation_corpus_id`, `evaluation_corpus_path` |

## Public API

Repair requests are built with `ValidationRequest(profile_name="repair", ...)`
(or profile-agnostic service/CLI entry points). A dedicated
`build_repair_request` helper remains intentionally deferred; other profiles
expose named builders under `aiodoo_validation.api`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `AdapterProfile` | Repair structural + behavior pipelines |
| `capabilities/repair/` | Spec + `RepairRecordParser` |
| `CapabilityBehavioralOracle` | Shared behavior oracle (repair registration) |
| `ValidationRequest` | Request construction for repair runs |
