# Coding Validation Profile (Phase 4)

**Status:** Phase 4 — profile selection and ValidationPlan metadata only (no validation execution)

The **Coding Profile** is the first real validation profile. All coding-specific
policy lives under `profiles/coding/`. The Validation Engine remains generic.

## Architecture

```text
Validation Engine
    ↓ ProfileEnginePort
ProfileEngine
    ↓ ProfileResolver
CodingProfile
    ↓ plan builder
ValidationPlan
    ↓ attached to RunContext
Inference Runner (unchanged generic port)
```

The engine never branches on `"coding"`. It only calls `ProfileEnginePort.resolve_profile()`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `ProfileEnginePort` | Resolve profile + build plan |
| `ProfileResolver` | Map profile name → profile object |
| `CodingProfile` | Coding metadata, capabilities, pipeline placeholders |
| `ValidationPlan` | Immutable execution metadata (no execution) |
| `profiles/coding/compatibility.py` | Coding artifact/model/adapter policy |
| `profiles/coding/policy.py` | Coding allowlists and rejected families |

## ValidationPlan

`ValidationPlan` describes future execution without running validation:

- Profile name and deterministic `plan_digest`
- `ProfileCapabilities` (inference on; oracles/scoring/benchmark/certification off)
- Supported artifact types and runtimes
- Placeholder pipelines (oracle, scoring, benchmark, certification)
- `execution_order` and `validation_stages`
- Frozen `configuration` snapshot (tier, protocol, Odoo versions, bundle digest)

## Compatibility ownership (post Phase 4)

| Layer | Validates |
|-------|-----------|
| **Artifact Resolution** | Protocol, metadata integrity, paths, fingerprints, duplicates |
| **Coding Profile** | Model family, adapter_type, coding policy, profile protocol scope |
| **Inference Runtime** | Runtime load prerequisites (base + adapter artifacts, Qwen runtime scope) |

Coding policy was moved **out of** resolution and inference into `profiles/coding/`.

## Rejected profiles and adapters

Rejected profile names: `planner`, `repair`, `conversation`, `execution`, `evaluation`.

Only `coding` is supported. Structured `ProfileError` codes are returned; the engine never crashes.

## RunContext integration

After successful `resolve_profile`:

- `validation_profile: ResolvedProfile` (concrete `CodingProfile`)
- `validation_plan: ValidationPlan`

Downstream phases should consume these objects instead of re-reading `ValidationRequest` for profile semantics.

## Relationship with Inference Runner

Inference validates **runtime** compatibility only (Qwen3-8B load prerequisites).
Coding adapter **policy** is enforced by the profile stage before inference runs.

No validation, oracle, scoring, benchmark, or certification logic executes in Phase 4.
