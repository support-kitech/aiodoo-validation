# Coding Validation Profile

**Status:** Production coding profile active (structural + behavioral Capability Delivery)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

> **Note:** Passages below that describe “Phase 5/6 placeholder oracles/scoring”
> are **historical**. Production structural and behavioral stages are active on the
> filesystem CLI path.

The **Coding Profile** is a first-class validation profile. Coding-specific
policy lives under `profiles/coding/`. The Coding **Capability Pack** lives
under `capabilities/coding/` (specification, parser, registration) — the same
foundation pattern as Repair.

Behavioral validation reuses the Validation Framework spine used by Repair
(`CapabilityBehavioralOracle`, corpus pins, behavioral scoring, behavior-gated
certification, report templates). Coding-specific pieces are IDs, pack/parser,
corpus pin, and profile pipeline stage registration.

## Architecture

```text
Validation Engine
    ↓ ProfileEnginePort
ProfileEngine
    ↓ ProfileResolver
CodingProfile
    ↓ plan builder (+ corpus resolution)
ValidationPlan
    ↓ attached to RunContext
Inference Runner
    ↓
Oracle Framework
  → structural production oracles
  → coding.oracle.behavior.coding (corpus-gated)
    ↓
Scoring → Benchmark → Certification → Report
  (structural + coding.behavior chain)
```

The engine never branches on `"coding"`. It only calls `ProfileEnginePort.resolve_profile()`.

Capability packs register via `capabilities/bootstrap.py` into
`CapabilityRegistry`. Coding and Repair packs are both registered for production
behavioral evaluation.

## Behavior lifecycle

```text
Request metadata
  → evaluation_corpus_id / evaluation_corpus_path
  → CodingProfile plan builder resolves corpus configuration
  → CapabilityBehavioralOracle (coding)
  → Coding Capability Pack + CodingRecordParser
  → ParsedCapabilityRecord → BehaviorCaseBuilder
  → BehaviorRunner (inference + comparators)
  → BehavioralEvidenceScorePolicy (coding.score.behavior)
  → coding.benchmark.behavior
  → BehaviorGatedCertificationPolicy (coding.certification.behavior)
  → coding.report.behavior
```

Without corpus id/path configuration, the behavior oracle **defers** (success with
`deferred=True`). Structural certification remains unchanged. Invalid corpus paths
or gate failures produce hard oracle errors.

## Behavior scoring

`BehavioralEvidenceScorePolicy.create_for_coding()` reuses the shared evidence
interpreter and scoring policy loader. Dimensions interpreted from oracle
metadata include transform correctness, pass rate / behavior, and related
extras already emitted by the capability behavior pipeline. No separate scoring
engine exists for Coding.

## Behavior certification

`BehaviorGatedCertificationPolicy.create_for_coding()` gates certification on
behavioral score signals exactly as Repair does, using Coding stage IDs:

| Stage | ID |
|-------|----|
| Oracle | `coding.oracle.behavior.coding` |
| Score | `coding.score.behavior` |
| Benchmark | `coding.benchmark.behavior` |
| Certification | `coding.certification.behavior` |
| Report | `coding.report.behavior` |

## Corpus requirements

| Item | Value |
|------|-------|
| Builtin pin id | `fixture.coding.eval.behavior` |
| Aliases | `coding.eval`, `coding.eval.fixture` |
| Fixture location | `tests/fixtures/capabilities/coding/eval_corpus/` |
| Role | `evaluation` (training corpora are gated out) |
| Request keys | `evaluation_corpus_id`, `evaluation_corpus_path` |

Records must parse through `CodingRecordParser` / the Coding Capability Pack.
Capability id on the corpus manifest must be `coding`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `ProfileEnginePort` | Resolve profile + build plan |
| `ProfileResolver` | Map profile name → profile object |
| `CodingProfile` | Coding metadata, capabilities, full pipelines |
| `ValidationPlan` | Immutable execution metadata |
| `profiles/coding/compatibility.py` | Coding artifact/model/adapter policy |
| `profiles/coding/policy.py` | Coding allowlists and rejected families |
| `capabilities/coding/` | Capability Specification + `CodingRecordParser` |
| `CapabilityBehavioralOracle` | Shared behavior oracle (coding registration) |
| `api.build_coding_request` | Public request builder (optional metadata) |

## ProfileEngine coupling note

`ProfileEngine` retains a single `isinstance(CodingProfile)` dispatch for
compatibility validation and plan construction. Coding-specific work is
delegated to `CodingProfile.validate_compatibility()` and
`CodingProfile.build_validation_plan()`.

## Oracle pipeline (metadata owned by Coding Profile)

```text
Metadata Oracle
  → Manifest Oracle
  → Python Oracle
  → XML Oracle
  → Security Oracle
  → Module Structure Oracle
  → Future Quality Oracle (disabled)
  → Coding Behavior Oracle (corpus-gated)
```

## ValidationPlan

`ValidationPlan` describes execution without implementing rules:

- Profile name and deterministic `plan_digest`
- `ProfileCapabilities` (inference + oracles + scoring + benchmark + certification + reports)
- Supported artifact types and runtimes
- Oracle / scoring / benchmark / certification / report pipelines
- `execution_order` and `validation_stages`
- Frozen `configuration` snapshot (includes corpus resolution when configured)

## Compatibility ownership (post Phase 4)

| Layer | Validates |
|-------|-----------|
| **Artifact Resolution** | Protocol, metadata integrity, paths, fingerprints, duplicates |
| **Coding Profile** | Model family, adapter_type, coding policy, profile protocol scope |
| **Inference Runtime** | Runtime load prerequisites (base + adapter artifacts, Qwen runtime scope) |
| **Oracle Framework** | Executes plan oracles only — no coding policy ownership |

Coding policy lives under `profiles/coding/` (formerly `domain/v1_scope.py`).

## Rejected profiles and adapters

Rejected profile names: `planner`, `repair`, `conversation`, `execution`, `evaluation`.

Only `coding` is supported. Structured `ProfileError` codes are returned; the engine never crashes.

## RunContext integration

After successful `resolve_profile`:

- `validation_profile: ResolvedProfile` (concrete `CodingProfile`)
- `validation_plan: ValidationPlan`

After successful oracle execution (Phase 5):

- `oracle_execution: OracleExecutionResult`

## Relationship with Inference Runner

Inference validates **runtime** compatibility only (Qwen3-8B load prerequisites).
Coding adapter **policy** is enforced by the profile stage before inference runs.
Behavioral oracles use the active inference session when a corpus is configured.
