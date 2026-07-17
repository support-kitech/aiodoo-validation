# Architecture (summary)

**Status:** Frozen — see ecosystem architecture and Technical Design documents.

`aiodoo-validation` is the **Canonical Evaluation & Certification Framework for AIODOO Models**.

## Responsibility

Determine whether a trained AIODOO model is suitable for production through validation, benchmarking (future), and certification (future).

## Logical architecture (Phase 1)

```
Validation Engine
    → Artifact Resolver (stub)
    → Profile Engine (stub)
    → Inference Runner (stub)
    → Validation Runner (stub)
    → Scoring Engine (stub)
    → Benchmark Engine (stub)
    → Certification Engine (stub)
    → Report Generator (stub)
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
