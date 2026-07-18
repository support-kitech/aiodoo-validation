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
| Current execution phase | **Phase 11 — Final Release Audit** — repository permanently frozen for **v1.x** maintenance |
| Structural / artifact validation | **Active (production)** |
| Behavioral validation | **All seven profiles wired** (approval/coding/conversation/evaluation/execution/planner/repair) — deferred without corpus id/path; active when configured |
| Approval Capability Pack | **Complete** |
| Coding Capability Pack | **Complete** |
| Conversation Capability Pack | **Complete** |
| Evaluation Capability Pack | **Complete** |
| Execution Capability Pack | **Complete** |
| Planner Capability Pack | **Complete** |
| Repair Capability Pack | **Complete** |
| Certification | **Structural + full behavior gates for all seven profiles** |
| Repository | Spec v1.0 authoritative; E0–E8 frozen; R1+RC1+RC2 complete; Capability Delivery complete; Phase 10 consolidation done; **Phase 11 freeze confirmed** |

---

## Current production capability

| Area | Status |
|------|--------|
| CLI / public API | Stable |
| Adapter profiles | approval, coding, conversation, evaluation, execution, planner, repair |
| Execution tiers | standard (no cert), smoke, full, prod alias |
| Structural oracles | Active |
| Behavioral oracles in production plans | **All seven profiles** — deferred without corpus; gated by `evaluation_corpus_id` / `evaluation_corpus_path` |
| Scoring | Structural 100/0; **all-profile behavioral multi-dimension** from oracle evidence (E6) |
| Corpus governance | **Pinned identities** via `CorpusPinRegistry` / `ProductionCorpusLookup` (E7); fixture pins for all seven profiles |
| Benchmark / certification | Structural + **all-profile behavior-gated cert** from ScoreResult (E8) |
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
| E5 behavior wiring | **Done / frozen** — CapabilityRegistry, ConfigurableCorpusProvider, production oracles for all seven profiles |
| E6 scoring extras | **Done / frozen** — evidence interpretation, policy loader, `BehavioralEvidenceScorePolicy` |
| E7 eval corpus pin | **Done / frozen** — pin registry, identity→path resolution, fixture pins for all seven profiles |
| E8 behavior-gated cert | **Done / frozen** — `BehaviorGatedCertificationPolicy`, criteria reasons, ScoreResult signals |
| R1 production hardening | **Done** — typing, layering cleanup, wiring consistency tests, docs |
| RC1 release validation | **Done** — quality gates green; source-tag packaging policy confirmed |
| RC2 final release audit | **Done** — contracts inventoried; maintenance policy published; GO for tag |
| Phase 10 consolidation | **Done** — profile parity audit, docs sync, deterministic ordering |
| Phase 11 final release audit | **Done** — production audit green; permanently frozen for v1.x maintenance |

---

## Release readiness (R1 / RC1 / RC2)

| Check | Status |
|-------|--------|
| Full unit/integration suite | Green (662 passed) |
| ruff check | Green |
| ruff format | Green |
| mypy strict | Green |
| coverage | ≥85% (85%) |
| Public API surface (`aiodoo_validation.api`) | Stable; internals not exported |
| Delivery chain IDs (all profiles) | Aligned (oracle→score→bench→cert→report) |
| Capability Delivery redesign | **Forbidden** — frozen |
| PyPI `[build-system]` wheel | **Out of scope** (intentional tooling-only pyproject) |
| Recommended publish | **git tag `v1.0.0`** source release |
| RC2 recommendation | **GO** for `v1.0.0` git tag (NO-GO for PyPI wheel under policy) |
| Known deferred (non-blocking) | `aiodoo-datasets` validation-layout pins; `build_repair_request`; content fingerprints |

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
- [MAINTENANCE.md](MAINTENANCE.md) — **v1.0.x maintenance policy**  
- Profile docs: [approval](approval_profile.md), [coding](coding_profile.md), [conversation](conversation_profile.md), [evaluation](evaluation_profile.md), [execution](execution_profile.md), [planner](planner_profile.md), [repair](repair_profile.md)

## Historical (do not treat as live Capability Delivery plan)

- [architecture_audit.md](architecture_audit.md)  
- [artifact_bundle.md](artifact_bundle.md) (historical Artifact Resolution “Phase 2”)  
- Chat roadmap P0–P14 (superseded by EEP)

---

## Explicitly not done yet

- Held-out evaluation corpora published from `aiodoo-datasets` in validation corpus package layout  
- Semantic / AI similarity comparators  
- `merged` / `foundation` profiles  
- Pack-local scoring policy files (E6 ships scoring defaults for known refs)  
- Edit-distance / syntax evidence in oracle metadata (dimensions stay deferred until evidence exists)  
- Coding Quality Oracle pipeline (still disabled placeholder stage)  
- Dedicated `build_repair_request` public helper (optional convenience; other builders exist)

---

## Maintenance rule

Do not add new top-level pipeline stages or redesign the CLI. Extend ports,
registries, and domain types inside the frozen Protocol V1 lifecycle.
Follow [delivery_governance.md](delivery_governance.md) and
[MAINTENANCE.md](MAINTENANCE.md).

**v1.0.x allowed:** bug fixes, security fixes, documentation, test coverage, and
capability pack registration via the existing pack contract that reuses the
frozen Capability Delivery spine (all seven adapter profiles are complete).

**v1.0.x forbidden:** architecture changes, new profiles beyond the frozen set,
feature work framed as Capability Delivery redesign.

---

## Freeze statements

- **Protocol V1 / structural certification path:** frozen and active.  
- **Specification Version 1.0 (docs):** frozen in this repository.  
- **Capability Delivery code:** E0–E8 frozen (spine complete; all seven profiles).  
- **R1 / RC1 / RC2:** hardening + release validation + final audit only — no Capability Delivery architecture changes.  
- **Phase 10:** consolidation / documentation / ordering only — no new validation features.  
- **Phase 11:** final release audit confirmed — permanently frozen for **v1.x** maintenance.  
- **v1.0.0 distribution:** source / git-tag (not PyPI wheel).  
- **Post-tag posture:** permanent maintenance mode for **v1.0.x**.
