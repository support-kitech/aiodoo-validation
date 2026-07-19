# Structural vs Behavioral Validation

**Status:** Architecture complete for both. All **seven** adapter profiles register
behavioral oracles; certification is **corpus-gated** (deferred without corpus).  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md) · **Contract:** [capability_validation_contract.md](capability_validation_contract.md).

This document distinguishes structural checks (always attempted) from behavioral
evaluation (attempted when an evaluation corpus is configured).

## Two validation kinds

| Kind | Purpose | Current production status |
|------|---------|---------------------------|
| **Artifact / Structural validation** | Verify on-disk contracts (`artifact.json`, adapter config, weights, metadata alignment) | **Active** — drives scoring, benchmark, and certification |
| **Behavior validation** | Prompt → inference → expected vs generated → comparator → score | **Wired for all seven profiles**; **deferred** when no corpus id/path is configured |

```text
Artifact Validation (structural oracles)
    ↓
Score / Benchmark / Certification (structural signals; behavior gates when corpus present)

Behavior Validation (behavioral oracles + BehaviorRunner) — seven profiles
    ↓
Comparator framework
    ↓
Score dimensions (behavior / weighted)
    ↓
Certification criteria (require_behavior_pass when corpus configured)
```

These are **not** separate CLI commands. Both plug into the existing
`RUN_VALIDATION` oracle pipeline via `Oracle` implementations tagged with
`ValidationKind.STRUCTURAL` or `ValidationKind.BEHAVIORAL`.

## Structural certification

Smoke / full / prod may grant `<profile>-certified` when structural oracles pass
and benchmarks meet thresholds. Without a corpus, behavior status is
`BehaviorStatus.DEFERRED` (`"deferred"`) and certification does not claim
behavioral competence.

Standard tier never production-certifies (framework wiring only).

Structural certification does **not** mean the model behaves correctly on Odoo
tasks. It means published artifacts satisfy the structural contract.

## Behavior certification (corpus-gated)

When evaluation corpora are attached:

1. `BehaviorCorpus` supplies real cases (never invented by validation).
2. `BehaviorRunner` generates with the initialized inference runner.
3. Comparators (exact, normalized text, …) produce `BehaviorResult`.
4. Behavioral oracles emit oracle results with `validation_kind=behavioral`.
5. Scoring records behavior dimensions; certification criteria can require
   `require_behavior_pass=True` per profile policy.

Without corpus config, behavioral oracles remain registered but evaluation is
**deferred** — not silently treated as a pass.

There is **no** `context` validation profile in v2.0.0 (intentional; see
`AUDIT_RESOLUTION.md`).

## Packages

| Package | Role |
|---------|------|
| `aiodoo_validation.domain.behavior` | Prompt, expected/generated output, cases, corpus, suite results |
| `aiodoo_validation.domain.comparator` | Comparator metadata/results |
| `aiodoo_validation.comparators` | Exact, normalized, AST, XML, JSON, token similarity; semantic/rule deferred |
| `aiodoo_validation.behavior` | `BehaviorRunner` |
| `aiodoo_validation.oracles.behavioral` | `BehavioralOracle` architecture |
| `aiodoo_validation.oracles.structural` | Production structural oracles |
| `aiodoo_validation.scoring.dimensions` | Multi-dimensional score architecture |
| `aiodoo_validation.certification.criteria` | Reusable certification criteria |

## Execution tiers

| Tier | Inference | Structural | Behavior corpus | Certification |
|------|-----------|------------|-----------------|---------------|
| `standard` | Stub | Wiring / structural checks | Limit `0` (not attempted) | Never |
| `smoke` | Real (Qwen → mock fallback) | Active | Soft limit (8) when corpus exists | Allowed |
| `full` / `prod` | Real | Active | No soft limit when corpus exists | Allowed |

## What we deliberately do not do

- Invent evaluation gold inside this repository
- Fake semantic similarity scores
- Claim train-all-8 ecosystem readiness from structural cert alone
- Add `merged` / `foundation` / `context` profiles in this freeze
