# Structural vs Behavioral Validation

**Status:** Architecture complete for both; production certification is structural today.

This document distinguishes what the framework **does now** from what it is
**ready to do** once evaluation corpora exist.

## Two validation kinds

| Kind | Purpose | Current production status |
|------|---------|---------------------------|
| **Artifact / Structural validation** | Verify on-disk contracts (`artifact.json`, adapter config, weights, metadata alignment) | **Active** — drives scoring, benchmark, and certification |
| **Behavior validation** | Prompt → inference → expected vs generated → comparator → score | **Architecture ready** — no corpora loaded; not enabled in production plans |

```text
Artifact Validation (structural oracles)
    ↓
Score / Benchmark / Certification (structural signals)

Behavior Validation (behavioral oracles + BehaviorRunner)
    ↓
Comparator framework
    ↓
Score dimensions (behavior / weighted)
    ↓
Certification criteria (optional behavior gates — off by default)
```

These are **not** separate CLI commands or pipeline stage renames. Both plug into
the existing `RUN_VALIDATION` oracle pipeline via `Oracle` implementations tagged
with `ValidationKind.STRUCTURAL` or `ValidationKind.BEHAVIORAL`.

## Structural certification (today)

Smoke / full / prod may grant `<profile>-certified` when structural oracles pass
and benchmarks meet thresholds.

Standard tier never production-certifies (framework wiring only).

Structural certification does **not** mean the model behaves correctly on Odoo
tasks. It means published artifacts satisfy the structural contract.

## Behavior certification (roadmap)

When evaluation corpora are attached:

1. `BehaviorCorpus` supplies real cases (never invented by validation).
2. `BehaviorRunner` generates with the initialized inference runner.
3. Comparators (exact, normalized text, …) produce `BehaviorResult`.
4. Behavioral oracles emit oracle results with `validation_kind=behavioral`.
5. Scoring records behavior dimensions; certification criteria can require
   `require_behavior_pass=True` per profile policy.

Until then, behavioral oracles remain **unregistered** in
`ProductionPipelineComponents`, and reports mark behavior validation as
`deferred_no_corpus`.

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

- Invent evaluation datasets or expected outputs
- Fake semantic / AI similarity scoring
- Claim behavioral certification while only structural checks run
- Redesign the CLI or pipeline stage order
