# Delivery Governance

**Status:** Frozen (Spec v1.0)  
**Index:** [SPECIFICATION_V1.md](SPECIFICATION_V1.md)  
**Execution:** [engineering_execution_plan.md](engineering_execution_plan.md)

Permanent engineering rules for `aiodoo-validation`. Architecture and EEP remain frozen; this document governs *how* we implement.

---

## Engineering principles

1. Frozen architecture wins (Protocol V1, CLI, DI topology, cert workflow).  
2. Honesty over capability theater (structural ≠ behavioral cert).  
3. Fail closed on trust boundaries (corpus role, fingerprints, bad paths).  
4. Capability-generic core; pack-local specifics.  
5. Small, revertable vertical slices (EEP).  
6. Tests are part of the product.  
7. Boring over clever (YAGNI).  
8. Compatibility by default (additive > breaking).  
9. Challenge incorrect instructions — correctness > agreement.  
10. No untracked technical debt that affects cert honesty.

---

## Definition of Ready (DoR)

Before coding an EEP phase:

1. Phase id in PR title (`E1: …`).  
2. EEP dependencies merged to `main`.  
3. Files MUST NOT change list acknowledged.  
4. Test plan sketched.  
5. No open architecture questions.  
6. E5+: structural golden strategy agreed.  
7. E8: written approval link exists.

If DoR fails → do not start; clarify first.

---

## Definition of Done (DoD)

1. Typecheck / compile per repo standards.  
2. All existing tests pass; new tests for new logic.  
3. No TODO / placeholder / dead code / `NotImplemented` on shipped paths.  
4. No duplicated logic.  
5. `CHANGELOG.md` for user- or cert-visible changes.  
6. `implementation_status.md` when behavior/cert/corpus meaning changes.  
7. PR states EEP phase, risk, rollback, test evidence.  
8. Review checklist completed.  
9. Backward compatible per public API policy.  
10. Revert plan stated.

---

## Quality gates (hard fail)

| Gate | Rule |
|------|------|
| G1–G3 | No TODOs, placeholders, dead code |
| G4 | No duplicated framework/pack logic |
| G5 | No silent swallowed trust/IO errors |
| G6 | No breaking public API without major + migration |
| G7 | No architecture/pipeline/CLI/DI change without ADR + unfreeze |
| G8–G9 | Independently testable and revertable |
| G10 | Train corpus cannot be used as evaluation |
| G11 | Default production without corpus: structural cert unchanged (E5+) |
| G12 | `require_behavior_pass` false until E8 approval |
| G13 | Capability schema only under `capabilities/<id>/` |
| G14 | Replace-only transforms until justified |
| G15 | Required CI green |

**Soft:** new dependencies, labeled skips for optional integration, large PRs, new env vars — must justify and document.

---

## Branch and merge

- `main` always releasable for structural cert.  
- One EEP phase per PR (docs-only exceptions OK).  
- **E5 rule:** If PR touches `production.py` **and** adds large new surface → **mandatory** E5a (libraries) + E5b (`production.py` + goldens).  
- No force-push to `main`; no merge on red CI.  
- Elevated review for `production.py`, certification criteria, CLI, public API (two reviewers or staff + risk note).  
- E8 requires product/tech lead approval.

---

## Testing

- Unit tests for gates, transforms, parser, metrics, builder.  
- Synthetic fixtures only — never vendor full training JSONL.  
- E5+: structural certification goldens for `repair` and `coding`.  
- Integration optional, marked, skippable without secrets.  
- Forbidden: inventing behavioral gold for cert claims; default-on network.

---

## Public API and compatibility

| Surface | Stability |
|---------|-----------|
| CLI | Stable (additive in 1.x) |
| `aiodoo_validation.api` | Stable |
| Exported `domain` types | Additive preferred |
| `capabilities` / `corpus` / `transforms` | Evolving; no silent breaks |

Deprecate ≥1 minor before removal. Cert label meaning must not silently expand from structural to behavioral.

---

## Cross-cutting policies (summary)

- **Architecture change:** ADR + unfreeze; default reject in feature PRs.  
- **Refactor:** Only in files already touched; no drive-by engine/CLI edits.  
- **Security:** No path escape; no executing generated shell/SQL in v1; no secrets in logs.  
- **Errors:** No corpus configured → defer; bad path → error; fail closed on fingerprints.  
- **Config:** Document every env var; defaults preserve structural cert.  
- **Dependencies:** Justify, pin, license OK.  
- **Release:** Tag when behavioral story changes (E5/E8); release notes stay honest.

---

## Cursor challenge policy

Cursor **must challenge** (not silently comply) when detecting:

Architecture drift; over-engineering / YAGNI; pack logic in framework packages; train-as-eval; premature `require_behavior_pass`; breaking APIs; TODOs/placeholders; partial wiring; swallowed gate failures; insufficient tests; wrong EEP sequencing; duplicate abstractions; cert-meaning “quick fixes”; security issues.

**Challenge format:** what is wrong · why · risks · better alternative · tradeoffs.

**May continue** when change matches EEP, DoR met, gates pass, architecture untouched.

**Must stop** for E8 without approval, conflicting instructions, or genuine blockers against frozen architecture.

**Engineering correctness > agreeing with the user.**

---

## Decision matrix

| Decision | Human mandatory? |
|----------|------------------|
| Architecture / CLI / pipeline / DI redesign | **Yes** (ADR) |
| EEP implementation details | Review on PR |
| Public API break | **Yes** |
| E5 `production.py` | Elevated review |
| E8 behavior cert gate | **Yes** (product + tech) |
| New dependency | Prefer yes |

---

## Anti-patterns (never)

Architecture redesign mid-feature; temporary cert-changing flags; untested paths; inventing eval gold in this repo; train JSONL as eval; registering all-profile behavior oracles early; premature extra transform types; silent cert meaning changes; TODOs on `main`; giant mixed-phase PRs; path traversal; agreeing with instructions that violate this governance.

---

## PR review checklist

- [ ] Named EEP phase; no pipeline/CLI/DI redesign  
- [ ] Pack-only capability schema  
- [ ] Train/eval rules preserved  
- [ ] Tests + existing green; E5 goldens if applicable  
- [ ] Cert unchanged unless E8  
- [ ] Docs/CHANGELOG/status as required  
- [ ] Fail closed; no bare except; no secret logs  
- [ ] Rollback stated  

---

## References

- [engineering_execution_plan.md](engineering_execution_plan.md)  
- [capability_validation_contract.md](capability_validation_contract.md)  
- [architecture.md](architecture.md)
