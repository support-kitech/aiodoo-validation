# Implementation Status

**Repository version:** 1.0.0+  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md) (**frozen**)  
**Architecture:** Validation Protocol V1 pipeline and public CLI **frozen**  
**Capability Delivery:** [engineering_execution_plan.md](engineering_execution_plan.md) (**frozen plan**; E0–E8 code landed)

---

## Snapshot

| Area | Status |
|------|--------|
| Architecture | **Complete / frozen** |
| Planning / Spec v1.0 documentation | **Complete** (materialized in repo) |
| Capability Delivery implementation | **Complete (E0–E8)** |
| Current execution phase | **E8 frozen** — Capability Delivery spine complete |
| Structural / artifact validation | **Active (production)** |
| Behavioral validation | **Repair wired** — deferred without corpus id/path; active when configured |
| Certification | **Structural + repair behavior gate** (`BehaviorGatedCertificationPolicy`) |
| Repository | Spec v1.0 authoritative; E0–E8 **frozen** |

---

## Current production capability

| Area | Status |
|------|--------|
| CLI / public API | Stable |
| Adapter profiles | coding, planner, repair, conversation, execution, approval, evaluation |
| Execution tiers | standard (no cert), smoke, full, prod alias |
| Structural oracles | Active |
| Behavioral oracles in production plans | **Repair only** — deferred without corpus; gated by `evaluation_corpus_id` / `evaluation_corpus_path` |
| Scoring | Structural 100/0; **repair behavioral multi-dimension** from oracle evidence (E6) |
| Corpus governance | **Pinned identities** via `CorpusPinRegistry` / `ProductionCorpusLookup` (E7) |
| Benchmark / certification | Structural + **repair behavior-gated cert** from ScoreResult (E8) |
| Reports | Structural + behavior certification reasons (`criteria_reasons`) |
| Comparators | Exact, normalized, AST, XML, JSON, token similarity |

---

## Capability Delivery progress (EEP)

| Phase | Status |
|-------|--------|
| E0 docs (Spec materialization) | **Done** |
| E0 domain types | **Done** — E0.3 identity alignment (`CorpusManifest.capability_id`) |
| E0 status | **Frozen** |
| E1 corpus package | **Done / frozen** — gates, JsonlCorpusLoader, fixtures |
| E2 transforms package | **Done / frozen** — replace-only TransformationEngine + SnapshotComparator |
| E3 BehaviorCaseBuilder | **Done / frozen** — ParsedCapabilityRecord → BehaviorCase (+ snapshots) |
| E4 Repair Capability Pack | **Done / frozen** — RepairRecordParser, capability.yaml, pack registration |
| E5 behavior wiring | **Done / frozen** — CapabilityRegistry, ConfigurableCorpusProvider, repair-only production oracle |
| E6 scoring extras | **Done / frozen** — evidence interpretation, policy loader, `BehavioralEvidenceScorePolicy` |
| E7 eval corpus pin | **Done / frozen** — pin registry, identity→path resolution, fixture pin for repair |
| E8 behavior-gated cert | **Done / frozen** — `BehaviorGatedCertificationPolicy`, criteria reasons, ScoreResult signals |

---

## Documentation (authoritative)

- [SPECIFICATION_V1.md](SPECIFICATION_V1.md) — **start here**  
- [capability_validation_contract.md](capability_validation_contract.md)  
- [capability_specification.md](capability_specification.md)  
- [engineering_execution_plan.md](engineering_execution_plan.md)  
- [delivery_governance.md](delivery_governance.md)  
- [architecture.md](architecture.md)  
- [behavioral_validation.md](behavioral_validation.md)  
- [cli.md](cli.md)

## Historical (do not treat as live Capability Delivery plan)

- [architecture_audit.md](architecture_audit.md)  
- [artifact_bundle.md](artifact_bundle.md) (historical Artifact Resolution “Phase 2”)  
- Chat roadmap P0–P14 (superseded by EEP)

---

## Explicitly not done yet

- Held-out evaluation corpora published from `aiodoo-datasets` in validation corpus package layout  
- Semantic / AI similarity comparators  
- Behavior gates for non-repair adapter profiles (policy-ready; not registered)  
- `merged` / `foundation` profiles  
- Pack-local scoring policy files (E6 ships scoring defaults for known refs)  
- Edit-distance / syntax evidence in oracle metadata (dimensions stay deferred until evidence exists)  

---

## Maintenance rule

Do not add new top-level pipeline stages or redesign the CLI. Extend ports,
registries, and domain types inside the frozen Protocol V1 lifecycle.
Follow [delivery_governance.md](delivery_governance.md).

---

## Freeze statements

- **Protocol V1 / structural certification path:** frozen and active.  
- **Specification Version 1.0 (docs):** frozen in this repository.  
- **Capability Delivery code:** E0–E8 frozen (spine complete).
