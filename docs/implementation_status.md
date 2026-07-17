# Implementation Status

**Repository version:** 0.0.0-dev  
**Active phases:** Phase 0–4 (complete)  
**Architecture audit:** [Post Phase 0–3 audit](architecture_audit.md) — **frozen**

## Implemented

### Phase 4 — Coding Validation Profile

- `ProfileEnginePort` with `ProfileResolutionOutcome`
- `ProfileEngine`, `ProfileResolver`, `CodingProfile`
- Immutable `ValidationPlan` with capabilities and pipeline placeholders
- Coding compatibility moved from resolution/inference into `profiles/coding/`
- `RunContext.validation_profile` and `RunContext.validation_plan`
- Engine profile stage with graceful failure handling
- Unit tests: profile resolution, plan creation, compatibility, engine integration
- [Coding profile documentation](coding_profile.md)

### Phase 0–3

See prior sections in git history / prior status entries for repository foundation, validation engine, artifact resolution, and inference runner.

## Not implemented (next phases)

| Phase | Component |
|-------|-----------|
| 5 | Oracle Framework |
| 6 | Scoring Engine |
| 7 | Benchmark Engine |
| 8 | Certification Engine |
| 9 | Validation Protocol V1 reports |
| 10 | CLI |
| 11 | aiodoo-training / Colab integration |
| 12 | Production hardening |
| 13 | v1.0.0 release |

## Next phase

**Phase 5 — Oracle Framework** per frozen Implementation Plan.
