# aiodoo-validation — Audit Resolution (v2.0.0)

| Audit Finding | Category | Decision | Action | Reason | Implementation Required? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `.gitignore` `reports/` hides `aiodoo_validation/reports/` (clean-clone structure tests fail) | **Production Blocker** | Fix | Scope ignore to `/reports/`; track package stub | Required package layout must not be ignored | **YES** |
| Git tag `v1.0.0` predates Capability Delivery; docs claim v1.0.0 with E0–E8 while HEAD differs | **Production Blocker** | Fix | Bump to **2.0.0**, tag HEAD, CHANGELOG | Release identity must match tree | **YES** |
| `docs/behavioral_validation.md` says behavior unregistered / structural-only cert | **Bug** / **Documentation** | Fix | Align with seven-profile corpus-gated behavior | Docs contradict code | **YES** |
| `docs/cli.md` documents `pip install -e .` | **Documentation** | Fix | Clone-and-run / `PYTHONPATH=.` / `scripts/` | Packaging policy forbids build-system | **YES** |
| README / MAINTENANCE locked to v1.x only | **Documentation** | Fix | Record v2.0.0 tooling freeze; Protocol V1 still frozen | Honesty | **YES** |
| No `context` validation profile | **Intentional** / **Future Work** | Leave | Do not add profile | Training owns context capability; validation seven-profile freeze | **NO** |
| No `[build-system]` / not PyPI | **Intentional** | Leave | Keep | Policy | **NO** |
| Placeholder digests, stub oracles, deferred corpora | **Intentional** | Leave | Keep documented | Not fake production path | **NO** |
| Semantic comparators, PDF reports, held-out corpora | **Future Work** | Leave | No implement | Roadmap | **NO** |
| Training/model/core E2E product composition | **Out of Scope** | Leave | Other repos | Boundary | **NO** |
| Coverage exactly 85% thin modules | **Intentional** | Leave | Gate already green | Not a blocker | **NO** |
