# Conversation Validation Profile

**Status:** Production conversation profile active (structural + behavioral Capability Delivery)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

The **Conversation Profile** is a first-class adapter validation profile hosted by
`AdapterProfile` (same host as Repair and Planner). The Conversation **Capability Pack** lives
under `capabilities/conversation/` and follows the same Capability Delivery spine as
Repair, Coding, and Planner.

## Behavior lifecycle

```text
Request metadata
  → evaluation_corpus_id / evaluation_corpus_path
  → AdapterProfile plan builder resolves corpus configuration
  → CapabilityBehavioralOracle (conversation)
  → Conversation Capability Pack + ConversationRecordParser
  → ParsedCapabilityRecord → BehaviorCaseBuilder
  → BehaviorRunner
  → BehavioralEvidenceScorePolicy (conversation.score.behavior)
  → conversation.benchmark.behavior
  → BehaviorGatedCertificationPolicy (conversation.certification.behavior)
  → conversation.report.behavior
```

Without corpus id/path configuration, the behavior oracle **defers**. Invalid
corpus paths or gate failures produce hard oracle errors.

## Stage IDs

| Stage | ID |
|-------|----|
| Oracle | `conversation.oracle.behavior.conversation` |
| Score | `conversation.score.behavior` |
| Benchmark | `conversation.benchmark.behavior` |
| Certification | `conversation.certification.behavior` |
| Report | `conversation.report.behavior` |

## Corpus

| Item | Value |
|------|-------|
| Builtin pin id | `fixture.conversation.eval.behavior` |
| Aliases | `conversation.eval`, `conversation.eval.fixture` |
| Fixture location | `tests/fixtures/capabilities/conversation/eval_corpus/` |
| Request keys | `evaluation_corpus_id`, `evaluation_corpus_path` |

## Public API

`api.build_conversation_request` builds a conversation `ValidationRequest` (optional
`metadata=` for corpus configuration).

## Components

| Component | Responsibility |
|-----------|----------------|
| `AdapterProfile` | Conversation structural + behavior pipelines |
| `capabilities/conversation/` | Spec + `ConversationRecordParser` |
| `CapabilityBehavioralOracle` | Shared behavior oracle (conversation registration) |
| `api.build_conversation_request` | Public request builder |
