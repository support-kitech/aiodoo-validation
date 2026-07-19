# aiodoo-validation — RELEASE_REPORT (v2.0.0)

**Release identity:** annotated tag `v2.0.0` (tooling freeze)  
**Protocol:** Validation Protocol V1 (major 1, frozen)  
**Date:** 2026-07-19

---

## Production Ready

| Question | Answer |
| --- | --- |
| In-boundary production ready (7 profiles)? | **YES** |
| `context` profile / cert? | **NO** (intentional) |
| Full ecosystem E2E cert claim? | **NO** |
| Production score (in-boundary) | **8 / 10** |

---

## Quality gates (local)

| Gate | Result |
| --- | --- |
| `ruff check .` | Pass |
| `ruff format --check .` | Pass |
| `mypy aiodoo_validation` | Pass (194 files) |
| `coverage run -m pytest` | **662 passed** |
| `coverage report --fail-under=85` | **85%** |
| `aiodoo_validation/reports/` tracked | Yes (not ignored) |

---

## Profiles

Registered: `approval`, `coding`, `conversation`, `evaluation`, `execution`,
`planner`, `repair`.

Not registered: `context`, `merged`, `foundation` (intentional).

Behavior: all seven wired; **corpus-gated** (deferred without corpus config).

---

## Ecosystem compatibility (read-only)

- Public API remains `aiodoo_validation.api` / `ValidationService`
- Training Capability Package consumers continue to use the seven adapter
  profile names; no breaking renames in this freeze
- Datasets sparse corpora do not invent gold inside validation (boundary held)

---

## Architecture impact

None. Protocol V1 and E0–E8 unchanged.

---

## Remaining blockers

None for in-boundary tooling freeze.

---

## Remaining future work

- `context` validation profile
- Held-out behavioral corpora; semantic comparators; rich report renderers
- Content fingerprint hashing beyond placeholder digests

---

## Architectural debt

- Placeholder content digests from artifact-resolution era
- Coverage cliff at exactly 85% (thin modules: inference runtime, some oracles)

---

## Repository health

**Strong** — gates green, docs aligned with seven-profile corpus-gated behavior,
clean-clone reports package trackable.

---

## Release recommendation

**Ship annotated tag `v2.0.0`**. Do not move historical `v1.0.0`. Do not claim
context certification or invent evaluation gold.
