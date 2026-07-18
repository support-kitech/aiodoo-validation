# Architecture Audit (Post Phase 0–3)

> **Historical document.** Snapshot from 2026-07-17 after Phases 0–3.
> For current production status see [implementation_status.md](implementation_status.md),
> [behavioral_validation.md](behavioral_validation.md), and
> [SPECIFICATION_V1.md](SPECIFICATION_V1.md).
> Do not treat Phase 0–3 “placeholder package” notes as the live CLI/filesystem path.
> Do not treat this document as the Capability Delivery plan (see EEP).

**Date:** 2026-07-17  
**Scope:** Phases 0–3 complete — pre–Phase 4 freeze review  
**Status:** Architecture considered stable for v1.0 implementation track

---

## 1. Architecture Score: **8.5 / 10**

The repository follows a clear hexagonal layout with immutable domain types, port-based dependency injection, and isolated ML runtime code. Minor v1-scope coupling and naming debt remain but do not require redesign before Phase 4–13.

---

## 2. Repository Strengths

| Area | Assessment |
|------|------------|
| **Layer separation** | Domain, ports, engine, resolution, inference, and stubs are distinct packages with clear roles. |
| **Dependency injection** | `ValidationEngine` accepts all collaborators via constructor; factories (`with_stubs`, `with_filesystem`, `with_mock_inference`) compose wiring. |
| **Immutability** | `ValidationRequest`, `RunContext`, `ArtifactBundle`, `InferenceSession`, and result types use frozen dataclasses with `with_*` updates. |
| **Graceful failure** | Artifact and inference stages return structured outcomes; engine never crashes on resolver/runner failures. |
| **ML isolation** | Torch / Transformers / PEFT imports exist only in `inference/runtime/qwen.py` (verified by boundary tests). |
| **Testability** | 81+ CPU-only tests; mock runtime default; fake artifact fixtures; no GPU or model downloads in CI. |
| **Documentation** | Phase-specific docs (`artifact_bundle.md`, `inference_runner.md`) plus implementation status tracking. |
| **Future placeholders** | Empty packages prepared for profiles, validation_plan, reports, benchmark, certification. |

---

## 3. Weaknesses

| Weakness | Severity | Notes |
|----------|----------|-------|
| **v1 coding scope embedded in resolution/inference** | Medium | Acceptable for v1-only repo; should migrate policy to profiles in Phase 4+. |
| **`PlaceholderStageResult` naming** | Low | Phase 0/1 name persists; real stage payloads now include structured data. |
| **Engine factory methods import concretes** | Low | Composition-root pattern; acceptable but couples engine module to implementations. |
| **`_artifact_paths` in bundle metadata** | Low | Practical inference bridge; documented as inference-only internal metadata. |
| **`StubInferenceRunner` wraps `RealInferenceRunner`** | Low | Slight indirection; keeps mock generation behavior consistent. |
| **No dedicated `scoring/` or `oracles/` placeholders yet** | Low | Ports exist in `ports/__init__.py`; packages can be added when Phase 5–6 starts. |

---

## 4. Technical Debt

| Item | Location | Recommendation |
|------|----------|----------------|
| Duplicated `REJECTED_ADAPTER_TYPES` | Was in 3 modules | **Fixed** — consolidated to `domain/v1_scope.py` |
| Resolution → inference import | Was in filesystem/stub resolvers | **Fixed** — path metadata moved to `domain/artifact_paths.py` |
| Coding profile checks in artifact resolution | `resolution/compatibility.py` | Move to `profiles/coding/` in Phase 4; keep v1 gate until then |
| Qwen/coding checks in inference | `inference/compatibility.py` | Split runtime scope (Qwen) vs profile scope (coding) in Phase 4 |
| `PlaceholderStageResult` | `domain/stage.py` | Rename to `StageResult` when report/CLI phases stabilize (non-urgent) |
| `validation_engine.py` size (334 lines) | `engine/` | Extract stage handlers to private module if it exceeds ~400 lines |
| Test-created fixture dirs under `tests/fixtures/artifacts/` | tests | Prefer `tmp_path` for mutable dirs (cosmetic cleanliness) |

---

## 5. Architecture Refinements Performed

| Refinement | Behaviour impact |
|------------|-------------------|
| Added `domain/v1_scope.py` — shared v1 constants | None |
| Added `domain/artifact_paths.py` — shared path metadata | None |
| Removed `resolution` → `inference` dependency | None |
| Added placeholder packages: `profiles/`, `validation_plan/`, `reports/`, `benchmark/`, `certification/` | None |
| Added `tests/unit/test_framework_boundaries.py` | None (new tests only) |

---

## 6. Architecture Refinements Intentionally NOT Performed

| Item | Reason |
|------|--------|
| Move coding compatibility out of resolution/inference | Requires Phase 4 profile engine; would change responsibility boundaries |
| Rename `PlaceholderStageResult` | Public type name; deferred to avoid unnecessary API churn |
| Split `ValidationEngine` stage handlers | File still manageable; no behaviour benefit |
| Add `oracles/` or `scoring/` packages | Ports already defined; packages added when implementation starts |
| Remove `_artifact_paths` from bundle metadata | Required bridge until opaque load handles exist |
| Extract composition root from engine | Factory methods are minimal; full DI container is over-engineering for v1 |

---

## 7. Remaining Coding-Specific Logic

| Location | What | Belongs in Phase 4? |
|----------|------|---------------------|
| `domain/request.py` | `SUPPORTED_PROFILES` = coding only | Partial — request validation stays; profile registry moves to profiles |
| `domain/enums.py` | `SupportedValidationProfile.CODING`, `ArtifactType.CODING_ADAPTER` | Enum stays; semantics owned by profile |
| `domain/v1_scope.py` | v1 adapter/model allowlists | Yes — migrate to profile policy |
| `resolution/compatibility.py` | Coding profile ↔ adapter_type checks | **Yes** |
| `resolution/common.py` | Rejects planner/repair/conversation/execution adapters | **Yes** (shared v1 policy until profiles exist) |
| `resolution/filesystem.py` | Expects `CODING_ADAPTER` artifact type | Partial — artifact kind vs profile policy |
| `inference/compatibility.py` | Requires coding adapter + Qwen3-8B | Split: Qwen stays in runtime; coding moves to profile |
| `inference/stub_runner.py` | Default `adapter_type="coding"` | Test/stub convenience — low priority |
| `stubs/__init__.py` | Passes `profile_name` in stub data | Harmless stub metadata |
| Tests & fixtures | coding adapter fixtures, planner rejection tests | Stay as test fixtures |

**No XML, Python, manifest, security, oracle, or scoring logic exists** — correct for Phase 3 boundary.

---

## 8. Recommendations for Phase 4

1. Implement `ProfileEnginePort` in `profiles/coding/` with validation plan selection.
2. Move profile ↔ artifact compatibility from `resolution/compatibility.py` into profile module; resolution validates structure/protocol only.
3. Introduce `ValidationPlan` domain type in `validation_plan/` (immutable, no execution logic yet).
4. Keep inference runtime scope (Qwen load/generate) separate from coding validation rules.
5. Add oracle package placeholder when Phase 5 starts; wire through `ValidationRunnerPort`.
6. Consider `StageResult` alias for `PlaceholderStageResult` before report generation (Phase 9).

---

## 9. Stable Enough for Version 1.0?

**Yes.** The repository architecture is stable enough that Phases 4–13 should implement capabilities inside the existing structure:

- Domain types and ports are established
- Engine orchestration pattern is proven
- Artifact and inference pipelines are isolated
- ML frameworks are confined to optional runtime
- Future packages have placeholder homes

No structural redesign is required before v1.0.

---

## 10. Should Redesign Ever Be Required Before v1.0?

**No full redesign should be necessary.** Incremental, behaviour-preserving refinements only:

| Possible minor adjustment | When |
|---------------------------|------|
| Profile policy extraction | Phase 4 |
| Stage result type rename | Phase 9 (reports) |
| Opaque artifact load handles (remove `_artifact_paths`) | When training export contract integrates (Phase 11) |
| Dedicated composition/bootstrap module | If factory count grows beyond ~5 |

A **full** architectural redesign before v1.0 would only be justified by a frozen TDD re-open — not by current technical debt levels.

---

## Dependency Direction (Verified)

```text
domain
  ↑
ports (protocols)
  ↑
resolution / inference / stubs / [future: profiles, oracles, …]
  ↑
engine (orchestration + composition factories)
```

**Verified absent from engine and domain:** Torch, Transformers, PEFT, filesystem (direct), oracles, scoring, reports, CLI.

**Verified confined:** Qwen HF runtime in `inference/runtime/qwen.py` only.

---

## Package Layout (Post-Audit)

```text
aiodoo_validation/
  domain/           # Immutable DTOs, enums, v1 scope, artifact path metadata
  ports/            # Protocol definitions
  engine/           # ValidationEngine orchestration
  resolution/       # Artifact resolution implementations
  inference/        # Inference runner + model runtimes
  stubs/            # Stub port bundle for CI
  profiles/         # Phase 4+ placeholder
  validation_plan/  # Phase 4+ placeholder
  reports/          # Phase 9+ placeholder
  benchmark/        # Phase 7+ placeholder
  certification/    # Phase 8+ placeholder
```

---

## SOLID Summary

| Principle | Status |
|-----------|--------|
| **S**ingle responsibility | Engine orchestrates; resolvers resolve; runners infer; domain holds data |
| **O**pen/closed | New profiles/runtimes via new port implementations |
| **L**iskov | Stub and real runners interchangeable via `InferenceRunnerPort` |
| **I**nterface segregation | Separate ports per downstream engine |
| **D**ependency inversion | Engine depends on ports, not concretes (except composition factories) |

---

## Testing & Documentation

- **81 tests passing** at audit time (includes 2 new boundary tests)
- Ruff + mypy strict clean
- Phase docs accurate; this audit doc added for freeze record

**Architecture is frozen for Phase 4 implementation.**

---

## Historical Annotation (Post Phase 4 — do not rewrite history)

> **Note (Phase 4 completion):** Responsibilities formerly owned by
> `domain/v1_scope.py` (v1 adapter/model allowlists, rejected adapter types)
> now live in `profiles/coding/policy.py`. The module `domain/v1_scope.py`
> was removed during Phase 4 when coding policy migrated into the Coding Profile.
>
> References to `domain/v1_scope.py` in sections 4–7 above are historical
> (accurate as of the post Phase 0–3 audit). They describe the pre–Phase 4
> state and are intentionally retained as the freeze record.
>
> Coding profile ↔ artifact compatibility formerly in `resolution/compatibility.py`
> and coding adapter policy formerly split across resolution/inference now live
> under `profiles/coding/`.