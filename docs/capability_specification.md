# Capability Specification

**Status:** Frozen (Spec v1.0)  
**Index:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)  
**Contract:** [capability_validation_contract.md](capability_validation_contract.md)

---

## Purpose

Declarative metadata contract for each capability (profile) supported by AIODOO Validation.

- **Owned by** the Capability Pack (instance file, e.g. `capabilities/repair/capability.yaml`).  
- **Schema rules owned by** the Capability Validation Contract.  
- **Consumed by** the framework (validation of corpus/transforms/dimensions ⊆ spec).  
- **Not** a second runtime engine.  
- **parser** is an **id/ref**, never an embedded executable in the spec document.

---

## Schema fields

| Field | Required | Notes |
|-------|----------|-------|
| `id` | Yes | Equals validation profile name (`repair`, …) |
| `name` | Yes | Human-readable |
| `description` | Yes | Short purpose |
| `version` | Yes | Spec instance version |
| `supported_artifact_types` | Yes | Align with framework artifact enums |
| `supported_languages` | Optional | e.g. `python`, `xml`, `yaml` |
| `supported_transformation_types` | Yes | e.g. `replace` for Repair v1 |
| `supported_comparator_kinds` | Yes | Subset of framework kinds |
| `supported_evaluation_dimensions` | Yes | Including `minimal_change` when applicable |
| `supported_certification_kinds` | Yes | `structural`, `behavioral` |
| `corpus_schema_id` | Yes | Schema id + version |
| `corpus_requirements` | Yes | Must require `role=evaluation` + fingerprint |
| `default_scoring_policy_ref` | Yes | Reference to pack policy data |
| `default_certification_policy_ref` | Yes | Reference to criteria defaults |
| `runtime_requirements` | Yes | e.g. real inference for behavior cert |
| `parser_id` | Yes | e.g. `repair_v1` — bound at registration |

---

## Example shape (Repair — illustrative)

```yaml
id: repair
name: Repair
description: Independent repair capability adapter validation
version: "1.0.0"
supported_artifact_types: [base_model, coding_adapter]
supported_languages: [python, xml]
supported_transformation_types: [replace]
supported_comparator_kinds: [exact, json, ast, xml, token_similarity]
supported_evaluation_dimensions:
  - transform_correctness
  - syntax
  - minimal_change
  - intent_preservation
  - hallucination
  - explanation
  - safety
supported_certification_kinds: [structural, behavioral]
corpus_schema_id: repair_tasks_v1
corpus_requirements:
  role: evaluation
  fingerprint_required: true
default_scoring_policy_ref: scoring_policy.yaml
default_certification_policy_ref: certification_defaults.yaml
runtime_requirements:
  behavior_certification: real_inference
parser_id: repair_v1
```

Instances are created in implementation **E4**. This document freezes the **schema**, not a checked-in YAML file yet.

---

## Relationship to validation profiles

| Concept | Role |
|---------|------|
| Validation profile (`--profile repair`) | CLI / engine profile name |
| `AdapterProfile` / `CodingProfile` | Resolve plan + structural compatibility |
| Capability Specification | Declares behavioral/corpus/transform metadata for Capability Delivery |

`id` **must** match the validation profile name.

---

## References

- [capability_validation_contract.md](capability_validation_contract.md)  
- [engineering_execution_plan.md](engineering_execution_plan.md) § E4  
- [SPECIFICATION_V1.md](SPECIFICATION_V1.md) glossary
