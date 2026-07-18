# Engineering Execution Plan (EEP)

**Status:** Frozen (Spec v1.0) — **canonical implementation sequence**  
**Index:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)  
**Governance:** [delivery_governance.md](delivery_governance.md)

Supersedes the chat **Implementation Roadmap (P0–P14)** for scheduling. Do not use P0–P14 phase numbers in PRs.

---

## Principles

1. Small production-ready phases; each independently mergeable and revertable.  
2. No TODOs, placeholders, dead code, or temporary abstractions.  
3. No ValidationEngine / CLI / pipeline / DI topology redesign.  
4. Prefer vertical slices over orphan APIs (e.g. gates+loader together).  
5. No unused modules (metrics wait until scoring has a consumer).

---

## Dependency graph

```text
E0  Spec docs + domain types
 │
 ├─► E1  Corpus (gates + JsonlCorpusLoader)
 │
 ├─► E2  Transforms (replace-only)          ← parallel with E1 after E0 types
 │
 E2 ─► E3  BehaviorCaseBuilder
 │
 E1+E2+E3 ─► E4  Repair Capability Pack
 │
 E1+E4 ─► E5  Behavior wiring (provider + repair-only production + provenance)
 │
 E2+E5 ─► E6  Edit metrics + scoring extras (cert gate still off)
 │
 External datasets ─► E7  Eval corpus pin
 │
 Product approval ─► E8  Behavior-gated certification
```

---

## Phases

### E0 — Spec materialization + domain types

| | |
|--|--|
| **Purpose** | Spec v1.0 docs in repo; then immutable domain types (`CorpusRole`, `CorpusManifest`, `CapabilitySpecification`, `ParsedCapabilityRecord`) |
| **This packaging task** | Documentation half of E0 (**no domain types in the docs-only PR if split**) |
| **MUST NOT change** | Engine, CLI, production wiring, oracles behavior |
| **Next** | Domain types under same E0 or immediate follow-up commit series |

### E1 — Corpus package

Gates + `JsonlCorpusLoader` + fixtures. Fail-closed train/eval. No Repair imports. Prefer concrete loader; Protocol only if needed.

### E2 — Transforms (replace-only)

`ArtifactSnapshot`, `ReplaceTransformation`, `TransformationEngine`, `SnapshotComparator` (delegates to existing comparators). Missing-search findings. **No** YAML/patch types yet.

### E3 — BehaviorCaseBuilder

`ParsedCapabilityRecord` → `BehaviorCase[]`. After E2 so encodings are not stubs. No Repair imports.

### E4 — Repair Capability Pack

`capabilities/repair/`: `RepairRecordParser`, `capability.yaml`, fixtures, pipeline tests. **Not** wired to production DI yet.

### E5 — Behavior wiring

`ConfigurableCorpusProvider` + **repair-only** behavioral oracle registration in `production.py` + report provenance. Default without corpus: deferred; structural cert unchanged. **Mandatory split** into E5a/E5b if `production.py` + large new surface co-land (see Governance).

### E6 — Edit metrics + scoring extras

Minimal Change / hallucination metrics; attach score extras when suite present. **`require_behavior_pass` still false**.

### E7 — Eval corpus pin

Pin held-out corpus from `aiodoo-datasets`; deny training fingerprints. Integration tests optional/skippable.

### E8 — Behavior-gated certification

Flip criteria only with **written human approval**. Mock runtime cannot satisfy behavior cert.

---

## What not to implement early

- Behavior oracles for all profiles before packs exist  
- Second transform types “for Linux”  
- Behavior-gated cert before E7+approval  
- Using `repair_v1_0.jsonl` training file as eval  

---

## References

- [delivery_governance.md](delivery_governance.md)  
- [capability_validation_contract.md](capability_validation_contract.md)  
- [implementation_status.md](implementation_status.md)
