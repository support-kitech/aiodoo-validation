# Implementation Status

**Repository version:** 0.0.0-dev  
**Active phases:** Phase 0–7 (complete)  
**Architecture audit:** [Post Phase 0–3 audit](architecture_audit.md) — **frozen**

## Implemented

### Phase 7 — Benchmark Engine

- `BenchmarkEnginePort` with `BenchmarkExecutionOutcome`
- `BenchmarkEngine`, `BenchmarkRegistry`, `BenchmarkPolicy` protocol
- Placeholder policies mapped 1:1 to frozen score IDs
- `RunContext.benchmark_execution` attachment
- Engine `BENCHMARK` stage wired through `BenchmarkEnginePort`
- Boundary tests: benchmark does not import oracle/scoring execution
- [Benchmark Engine documentation](benchmark_engine.md)

### Phase 0–6

Repository foundation, validation engine, artifact resolution, inference runner,
coding profile, oracle framework, scoring engine (frozen through Phase 6).

## Not implemented (next phases)

| Phase | Component |
|-------|-----------|
| 8 | Certification Engine |
| 9 | Validation Protocol V1 reports |
| 10 | CLI |
| 11 | aiodoo-training / Colab integration |
| 12 | Production hardening |
| 13 | v1.0.0 release |

## Next phase

**Phase 8 — Certification Engine** per frozen Implementation Plan.
