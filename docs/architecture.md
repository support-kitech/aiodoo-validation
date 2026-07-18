# Architecture (summary)

**Status:** Validation Protocol V1 pipeline frozen; production implementations evolve inside existing stages.

`aiodoo-validation` is the **Canonical Evaluation & Certification Framework for AIODOO Models**.

## Responsibility

Determine whether a trained AIODOO model is suitable for production through
validation, benchmarking, and certification.

## Logical architecture

```
External repository / User
    ↓
CLI or ValidationService (public API)
    ↓
Validation Engine
    → Artifact Resolver (filesystem)
    → Profile Engine → CodingProfile / AdapterProfile → ValidationPlan
    → Inference Runner (tier-aware: stub | Qwen | mock fallback)
    → Oracle Framework
         • Structural oracles (active production)
         • Behavioral oracles (architecture ready; corpora deferred)
    → Scoring Engine (dimensional metadata; primary score still 100/0 structural)
    → Benchmark Engine (threshold + optional runtime metrics)
    → Certification Engine (criteria + profile labels)
    → Report Generator (machine-readable structural/behavior summaries)
    ↓
ValidationRunResult → formatter (CLI or external consumer)
```

## Structural vs behavioral

See [behavioral_validation.md](behavioral_validation.md).

- **Artifact validation** — structural oracles on resolved artifacts
- **Behavior validation** — prompt/inference/comparator architecture (no fake datasets)

## Boundaries

| Repository | Relationship |
|------------|--------------|
| aiodoo-training | Consumes exported artifacts (read-only) |
| aiodoo-datasets | Consumes pinned eval fixtures (read-only, future) |
| aiodoo-colab | Orchestrates validation runs |
| aiodoo-core | Protocol alignment only — no runtime coupling |
| aiodoo-models | Promotion target for certification records (future) |

## Profiles

Supported adapter profiles share one architecture (`CodingProfile` + `AdapterProfile`):

`coding`, `planner`, `repair`, `conversation`, `execution`, `approval`, `evaluation`

Future `merged` / `foundation` profiles remain intentionally unsupported until designed.

## Compatibility

Do not redesign the frozen pipeline stage order or public CLI without an explicit
architecture re-open. Production work replaces placeholders **inside** existing ports.
