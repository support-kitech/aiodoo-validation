# Coding Validation Profile

**Status:** Production coding profile active (structural validation path)  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)

> **Note:** Passages below that describe “Phase 5/6 placeholder oracles/scoring”
> are **historical**. Production structural oracles and scoring are active on the
> filesystem CLI path. Capability Delivery for Repair and others follows the EEP,
> not a coding-only redesign.

The **Coding Profile** is the first real validation profile. Coding-specific
policy lives under `profiles/coding/`. Additional adapter profiles reuse
`AdapterProfile`. The Validation Engine remains generic.

## Architecture

```text
Validation Engine
    ↓ ProfileEnginePort
ProfileEngine
    ↓ ProfileResolver
CodingProfile / AdapterProfile
    ↓ plan builder
ValidationPlan
    ↓ attached to RunContext
Inference Runner
    ↓
Oracle Framework (structural production oracles)
```

The engine never branches on `"coding"`. It only calls `ProfileEnginePort.resolve_profile()`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `ProfileEnginePort` | Resolve profile + build plan |
| `ProfileResolver` | Map profile name → profile object |
| `CodingProfile` | Coding metadata, capabilities, oracle pipeline |
| `ValidationPlan` | Immutable execution metadata |
| `profiles/coding/compatibility.py` | Coding artifact/model/adapter policy |
| `profiles/coding/policy.py` | Coding allowlists and rejected families |

## ProfileEngine coupling note

`ProfileEngine` retains a single `isinstance(CodingProfile)` dispatch for
compatibility validation and plan construction. Coding-specific work is
delegated to `CodingProfile.validate_compatibility()` and
`CodingProfile.build_validation_plan()`. A broader profile-operations Protocol
was intentionally **not** introduced — only one profile exists today, and
premature abstraction would add complexity without architectural benefit.

## Oracle pipeline (metadata owned by Coding Profile)

```text
Metadata Oracle
  → Manifest Oracle
  → Python Oracle
  → XML Oracle
  → Security Oracle
  → Module Structure Oracle
  → Future Quality Oracle (disabled)
```

Phase 5 executes enabled stages via the Oracle Framework as placeholders only.
Phase 6 scores those oracle results via the Scoring Engine (deterministic placeholders).

## ValidationPlan

`ValidationPlan` describes execution without implementing rules:

- Profile name and deterministic `plan_digest`
- `ProfileCapabilities` (inference + oracles + scoring on; benchmark/certification off)
- Supported artifact types and runtimes
- Oracle / scoring / benchmark / certification pipelines
- `execution_order` and `validation_stages`
- Frozen `configuration` snapshot

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
