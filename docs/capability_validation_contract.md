# Capability Validation Contract

**Status:** Frozen (Spec v1.0)  
**Index:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)  
**Related:** [capability_specification.md](capability_specification.md) · [behavioral_validation.md](behavioral_validation.md)

---

## Purpose

Platform invariants for **every** capability validated by AIODOO Validation.

Repair is the first Capability Pack that implements this contract — not a special-case architecture.

---

## Integration spine (unchanged Protocol V1)

```text
Capability (profile name)
  → Evaluation Corpus (CorpusRole=evaluation, fingerprint)
  → RecordParser → ParsedCapabilityRecord
  → BehaviorCaseBuilder → BehaviorCase[]
  → BehaviorRunner + Inference
  → ComparatorRegistry (+ TransformationEngine when edits apply)
  → BehavioralOracle results
  → Scoring (dimensions + weights)
  → CertificationCriteria
  → Reporting (kind, labels, corpus provenance)
```

Structural validation continues via existing structural oracles. Behavioral work plugs into `RUN_VALIDATION` — **no new pipeline stages**.

---

## Hard rules

1. **No new pipeline stages** for a capability.  
2. **No train corpora for behavior certification** — `CorpusRole.evaluation` only; fingerprint deny-list vs training releases.  
3. **Empty / missing corpus ⇒ deferred**, never invent cases or gold labels.  
4. **Misconfigured corpus path ⇒ hard error**, not silent defer.  
5. **Capability-specific schema** lives only in the Capability Pack (e.g. `capabilities/repair/`).  
6. **Framework packages stay generic** (`corpus/`, `transforms/`, `behavior/` case builder).  
7. **Structural ≠ behavioral certification** — labels and reports must stay honest.  
8. **No cross-adapter weight chaining** in validation (adapters are independent capabilities).  
9. **`require_behavior_pass` stays false** until E8 + explicit human approval.  
10. **Replace-only** `TransformationEngine` until a second capability proves a new transform type is required.

---

## Ownership triangle

| Layer | Owns |
|-------|------|
| **Capability Validation Contract** (this doc) | Invariants; dimension *semantics* (including Minimal Change) |
| **Capability Specification** | Declarative per-capability metadata |
| **Capability Pack** | Parser, optional transforms mapping, scoring policy *data*, criteria defaults |
| **Framework** | Engine, oracles, BehaviorRunner, comparators, TransformationEngine, scoring/cert *engines*, reports |

---

## Evaluation dimensions (semantics)

Dimensions are scored when behavior runs; they do not invent values when deferred.

| Dimension | Meaning |
|-----------|---------|
| Transform / edit correctness | Generated transform or post-apply content matches gold |
| Syntax validity | Parsed language artifacts remain valid (e.g. AST) |
| Functional correctness | Runtime/harness — **deferred** until a real harness exists |
| Intent preservation | Non-target structure preserved |
| **Minimal Change** | Smallest sufficient edit; penalize unrelated churn |
| Explanation quality | Soft alignment with gold explanation |
| Hallucination | Missing search targets, invented paths |
| Safety / policy | Tag/rule-driven policy findings |
| Determinism | Policy attribute of comparators — not a scored “luck” dimension |

Formatting-only noise is a signal/warning, not a primary dimension.

---

## Train vs evaluation (fail-closed)

| Check | Production behavior |
|-------|---------------------|
| `CorpusRole` ≠ `evaluation` | Reject for production behavior |
| Fingerprint missing / mismatch | Reject |
| Fingerprint on training deny-list | Reject |
| No corpus configured | Defer behavioral evaluation |
| Path set but invalid | Error |

Datasets package publishes evaluation corpora; validation never invents them.

---

## How to add a future capability (checklist)

1. Write Capability Specification instance (`capability.yaml`).  
2. Implement RecordParser in `capabilities/<id>/`.  
3. Publish evaluation corpus + CorpusManifest.  
4. Optional: new `Transformation` type only if existing types insufficient.  
5. Pack scoring policy data.  
6. Wire corpus provider / registration per EEP — **no** ValidationEngine redesign.

---

## References

- [capability_specification.md](capability_specification.md)  
- [engineering_execution_plan.md](engineering_execution_plan.md)  
- [delivery_governance.md](delivery_governance.md)  
- [architecture.md](architecture.md)
