# Architecture (summary)

**Status:** Frozen — see ecosystem architecture and Technical Design documents.

`aiodoo-validation` is the **Canonical Evaluation & Certification Framework for AIODOO Models**.

## Responsibility

Determine whether a trained AIODOO model is suitable for production through validation, benchmarking, and certification.

## Logical architecture (Phase 10)

```
User
    ↓
CLI (validate | version | capabilities | help)
    ↓
Validation Engine
    → Artifact Resolver (filesystem + stub)
    → Profile Engine → Coding Profile → ValidationPlan
    → Inference Runner (mock default; optional Qwen runtime)
    → Oracle Framework (registry + placeholder oracles)
    → Scoring Engine (oracle results only; placeholder scores)
    → Benchmark Engine (score results only; placeholder comparisons)
    → Certification Engine (benchmark results only; placeholder certification)
    → Report Generator (certification results only; placeholder report objects)
    ↓
ValidationRunResult → ConsoleFormatter → Terminal output
```

## Boundaries

| Repository | Relationship |
|------------|--------------|
| aiodoo-training | Consumes exported artifacts (read-only) |
| aiodoo-datasets | Consumes pinned eval fixtures (read-only, future) |
| aiodoo-colab | Orchestrates validation runs (future) |
| aiodoo-core | Protocol alignment only — no runtime coupling |
| aiodoo-models | Promotion target for certification records (future) |

## v1 scope

Coding Validation only — Qwen3-8B + AIODOO Coding Adapter — Odoo 17/18/19.

Do not redesign this document without an explicit architecture re-open.
