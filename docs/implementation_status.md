# Implementation Status

**Repository version:** 0.0.0-dev  
**Active phases:** Phase 0–6 (complete)  
**Architecture audit:** [Post Phase 0–3 audit](architecture_audit.md) — **frozen**

## Implemented

### Phase 6 — Scoring Engine

- `ScoringEnginePort` with `ScoreExecutionOutcome`
- `ScoringEngine`, `ScoringRegistry`, `ScorePolicy` protocol
- Placeholder policies mapped 1:1 to frozen oracle IDs
- `RunContext.score_execution` attachment
- Engine `SCORING` stage wired through `ScoringEnginePort`
- Unit tests: registry, pipeline, engine integration, structured errors
- [Scoring Engine documentation](scoring_engine.md)

### Phase 5 — Oracle Framework

- Oracle runner, registry, placeholder oracles
- Frozen Oracle ID convention in `oracles/ids.py`
- [Oracle Framework documentation](oracle_framework.md)

### Phase 0–4

Repository foundation, validation engine, artifact resolution, inference runner,
coding validation profile.

## Not implemented (next phases)

| Phase | Component |
|-------|-----------|
| 7 | Benchmark Engine |
| 8 | Certification Engine |
| 9 | Validation Protocol V1 reports |
| 10 | CLI |
| 11 | aiodoo-training / Colab integration |
| 12 | Production hardening |
| 13 | v1.0.0 release |

## Next phase

**Phase 7 — Benchmark Engine** per frozen Implementation Plan.
