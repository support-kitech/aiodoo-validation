# Implementation Status

**Repository version:** 1.0.0+  
**Specification:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md) (**frozen**)  
**Architecture:** Validation Protocol V1 pipeline and public CLI **frozen**  
**Capability Delivery:** [engineering_execution_plan.md](engineering_execution_plan.md) (**frozen plan**; E0–E4 code landed)

---

## Snapshot

| Area | Status |
|------|--------|
| Architecture | **Complete / frozen** |
| Planning / Spec v1.0 documentation | **Complete** (materialized in repo) |
| Capability Delivery implementation | **In progress** |
| Current execution phase | **E4 frozen** — E5 next (behavior wiring; repair-only) |
| Structural / artifact validation | **Active (production)** |
| Behavioral validation | Architecture ready — **deferred** without evaluation corpora |
| Certification | **Structural only**; `require_behavior_pass` **off** |
| Repository | Spec v1.0 authoritative; E0–E4 Repair Capability Pack **frozen** |

---

## Current production capability

| Area | Status |
|------|--------|
| CLI / public API | Stable |
| Adapter profiles | coding, planner, repair, conversation, execution, approval, evaluation |
| Execution tiers | standard (no cert), smoke, full, prod alias |
| Structural oracles | Active |
| Behavioral oracles in production plans | Not loaded / deferred |
| Scoring | Structural 100/0 primary; dimensions architecture ready |
| Benchmark / certification | Structural signals |
| Reports | Structural + `behavior_status=deferred` when applicable |
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
| E5 wiring | Not started |
| E6 scoring extras | Not started |
| E7 eval corpus pin | Blocked on datasets eval publish |
| E8 behavior-gated cert | Not started (requires approval) |

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

- E5+ Capability Delivery (production behavior wiring, scoring extras, eval pin, cert gate)  
- Evaluation corpora loaded in production  
- Semantic / AI similarity comparators  
- Behavior-gated certification  
- `merged` / `foundation` profiles  

---

## Maintenance rule

Do not add new top-level pipeline stages or redesign the CLI. Extend ports,
registries, and domain types inside the frozen Protocol V1 lifecycle.
Follow [delivery_governance.md](delivery_governance.md).

---

## Freeze statements

- **Protocol V1 / structural certification path:** frozen and active.  
- **Specification Version 1.0 (docs):** frozen in this repository.  
- **Capability Delivery code:** E0–E4 frozen; continue at E5 (behavior wiring).
