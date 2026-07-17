# Implementation Status

**Repository version:** 0.0.0-dev  
**Active phases:** Phase 0–5 (complete)  
**Architecture audit:** [Post Phase 0–3 audit](architecture_audit.md) — **frozen** (annotated post Phase 4)

## Implemented

### Phase 5 — Oracle Framework

- `OracleRunnerPort` with `OracleExecutionOutcome`
- `OracleEngine`, `OracleRegistry`, `Oracle` protocol
- Domain types: `OracleResult`, `OracleExecutionResult`, `OracleContext`, errors
- Placeholder oracles: Metadata, Manifest, Python, XML, Security, Module Structure
- Coding Profile oracle pipeline metadata (Quality disabled / future)
- `RunContext.oracle_execution` attachment
- Engine `RUN_VALIDATION` stage wired through `OracleRunnerPort`
- Unit tests: registry, pipeline, engine integration, structured errors
- [Oracle Framework documentation](oracle_framework.md)

### Phase 4 — Coding Validation Profile

- Profile engine, Coding Profile, ValidationPlan, RunContext profile attachment
- Coding policy ownership under `profiles/coding/`
- Final refinements: profile method dispatch cleanup, audit historical annotation
- [Coding profile documentation](coding_profile.md)

### Phase 0–3

Repository foundation, validation engine, artifact resolution, inference runner.

## Not implemented (next phases)

| Phase | Component |
|-------|-----------|
| 6 | Scoring Engine |
| 7 | Benchmark Engine |
| 8 | Certification Engine |
| 9 | Validation Protocol V1 reports |
| 10 | CLI |
| 11 | aiodoo-training / Colab integration |
| 12 | Production hardening |
| 13 | v1.0.0 release |

## Next phase

**Phase 6 — Scoring Engine** per frozen Implementation Plan.
