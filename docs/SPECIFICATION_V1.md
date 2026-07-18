# AIODOO Validation Specification Version 1.0

**Status:** Frozen (documentation packaging complete)  
**Entry point:** This file is the canonical index for Spec v1.0.  
**Code implementation of Capability Delivery:** Not started — see [Engineering Execution Plan](engineering_execution_plan.md) phase **E0** (domain types next).

Do **not** redesign architecture, CLI, ValidationEngine pipeline, DI topology, or certification workflow in implementation PRs. See [Delivery Governance](delivery_governance.md).

---

## Purpose

This specification defines how `aiodoo-validation` evaluates AIODOO capability adapters (Repair first; Linux/Docker/Git/… later) while preserving the frozen Validation Protocol V1.

The repository must remain the **single source of truth**. Planning chat is not authoritative once documents land here.

---

## Architecture status

| Area | Status |
|------|--------|
| Validation Protocol V1 pipeline | **Frozen** |
| Public CLI / API | **Frozen** |
| Structural / artifact validation | **Active (production)** |
| Behavioral validation architecture | **Ready** (corpora not loaded) |
| Capability Delivery (EEP E0–E8) | **Planned** — implementation not started |
| Behavior-gated certification | **Off** until E8 + approval |

See [architecture.md](architecture.md) and [behavioral_validation.md](behavioral_validation.md).

---

## Frozen documents (authoritative)

| Document | Role |
|----------|------|
| [architecture.md](architecture.md) | Protocol V1 logical architecture |
| [behavioral_validation.md](behavioral_validation.md) | Structural vs behavioral honesty |
| [capability_validation_contract.md](capability_validation_contract.md) | Invariants for every capability |
| [capability_specification.md](capability_specification.md) | Declarative capability metadata schema |
| [engineering_execution_plan.md](engineering_execution_plan.md) | **Canonical** implementation sequence (E0–E8) |
| [delivery_governance.md](delivery_governance.md) | How we implement and review |
| [implementation_status.md](implementation_status.md) | Live status vs plan |

**Supersession rule:** The older chat **Implementation Roadmap (P0–P14)** is **not** an execution schedule. Only **EEP E0–E8** governs implementation order.

---

## Execution order (Capability Delivery)

```text
E0  Spec docs (this packaging) + domain types
E1  Corpus package (gates + JsonlCorpusLoader)     ║ parallel with E2 after E0 types
E2  Transforms (replace-only TransformationEngine) ║
E3  BehaviorCaseBuilder
E4  Repair Capability Pack (parser + capability.yaml + fixtures)
E5  Behavior wiring (provider + repair-only production registration + provenance)
E6  Edit metrics + scoring extras (no cert gate)
E7  Eval corpus pin (aiodoo-datasets)
E8  Behavior-gated certification (human approval required)
```

Details: [engineering_execution_plan.md](engineering_execution_plan.md).  
Process: [delivery_governance.md](delivery_governance.md).

---

## Document relationships

```text
SPECIFICATION_V1.md  (this index)
        │
        ├─► capability_validation_contract.md
        │         └─► capability_specification.md
        │                   └─► Capability Pack (code; E4+)
        ├─► engineering_execution_plan.md
        │         └─► delivery_governance.md
        ├─► architecture.md
        │         └─► behavioral_validation.md
        └─► implementation_status.md
```

---

## Glossary (canonical names)

| Canonical term | Meaning | Do not use |
|----------------|---------|------------|
| **Capability Pack** | Pack-local code + config for one profile (e.g. repair) | “Repair validator”, “Repair engine” |
| **Capability Specification** | Declarative metadata for a capability | — |
| **Capability Validation Contract** | Platform invariants for all capabilities | — |
| **BehaviorCase** / **BehaviorCorpus** / **BehaviorRunner** | Behavioral evaluation spine | — |
| **BehavioralOracle** | Oracle wrapping behavior runs | — |
| **TransformationEngine** | Applies transforms to snapshots | `OperationApplyComparator` |
| **ArtifactSnapshot** | Path-keyed content map | — |
| **ReplaceTransformation** | search/replace transform (first type) | “RepairOperation” |
| **SnapshotComparator** | Compares snapshots via existing comparators | — |
| **CorpusManifest** / **CorpusRole** | Corpus metadata; `evaluation` vs `training` | — |
| **capability_id** | Same identity as Spec `id` and CLI/validation `profile_name` on `CorpusManifest` and `ParsedCapabilityRecord` | Do not invent a second id |
| **JsonlCorpusLoader** | Generic JSONL + manifest loader | `JsonlBehaviorCorpusLoader` |
| **BehaviorCaseBuilder** | Parsed record → BehaviorCase[] | — |
| **RepairRecordParser** | Repair schema → ParsedCapabilityRecord | `RepairCaseAdapter` |
| **CertificationCriteria** | Reusable cert inputs | `RepairCertificationCriteria` type |
| **Capability scoring policy** | Pack-owned weights/data | `RepairScorePolicy` type |
| **EEP E0–E8** | Canonical execution phases | Roadmap P0–P14 |
| **Capability Delivery** | This workstream | Repo historical “Phase 2” (artifacts) |

---

## Implementation status (summary)

| Item | State |
|------|-------|
| Architecture | Complete / frozen |
| Planning / Spec v1.0 docs | **Complete** (this packaging) |
| Capability Delivery code | **Not started** |
| Current execution phase | **E0** (docs landed; domain types next) |
| Behavior in production | Architecture ready; **deferred** without corpus |
| Certification | **Structural** only; behavior gate off |

Full detail: [implementation_status.md](implementation_status.md).

---

## Historical documents (not current)

These remain for history. **Do not** treat them as the live Capability Delivery plan.

| Document | Note |
|----------|------|
| [architecture_audit.md](architecture_audit.md) | Post Phase 0–3 snapshot |
| [artifact_bundle.md](artifact_bundle.md) | Historical **Artifact Resolution** phase (also called “Phase 2” then) |
| [coding_profile.md](coding_profile.md) | Still useful for coding; some “placeholder Phase 5/6” text is historical |
| Chat “Implementation Roadmap P0–P14” | Superseded by EEP |

---

## Repository navigation

| Need | Go to |
|------|-------|
| Start here | This file |
| How capabilities plug in | [capability_validation_contract.md](capability_validation_contract.md) |
| Spec field schema | [capability_specification.md](capability_specification.md) |
| What to build next | [engineering_execution_plan.md](engineering_execution_plan.md) |
| PR / merge / challenge rules | [delivery_governance.md](delivery_governance.md) |
| Is behavior certifying? | [behavioral_validation.md](behavioral_validation.md) |
| Live status | [implementation_status.md](implementation_status.md) |
| CLI | [cli.md](cli.md) |

---

## Compatibility

Spec v1.0 does **not** change Validation Protocol V1, CLI, or public API. Capability Delivery extends **inside** existing ports and stages.
