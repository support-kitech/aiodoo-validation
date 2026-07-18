# Implementation Status

**Repository version:** 1.0.0+  
**Status:** Production validation engine evolving inside frozen Protocol V1  
**Architecture:** Pipeline stage order and public CLI frozen

## Current production capability

| Area | Status |
|------|--------|
| CLI / public API | Stable |
| Adapter profiles | coding, planner, repair, conversation, execution, approval, evaluation |
| Execution tiers | standard (no cert), smoke, full, prod alias |
| Structural / artifact validation | Active |
| Behavioral validation | Architecture ready — `BehaviorStatus.DEFERRED` without corpora |
| Scoring dimensions | Architecture + structural 100/0 primary score |
| Certification criteria | Reusable policy architecture; structural/benchmark signals |
| Reports | Machine-readable structural/behavior summaries + convenience fields |
| Comparators | Exact, normalized, AST, XML, JSON, token similarity; semantic/rule deferred |
| Extensibility metadata | Runtime metrics schema, comparator capabilities, versioned label helpers |

## Documentation

- [Architecture](architecture.md)
- [Structural vs Behavioral Validation](behavioral_validation.md)
- [Extensibility refinements](extensibility_refinements.md)
- [Oracle Framework](oracle_framework.md)
- [CLI](cli.md)

## Explicitly not done yet

- Domain Odoo behavioral corpora (Python/XML/security/conversation/…)
- Semantic / AI similarity comparators
- Behavior-gated certification (`require_behavior_pass`)
- `merged` / `foundation` profiles

## Maintenance rule

Do not add new top-level pipeline stages or redesign the CLI. Extend ports,
registries, and domain types inside the frozen Protocol V1 lifecycle.

## Freeze recommendation

**Ready to freeze** for v1.x **structural certification**.

Behavioral certification remains intentionally deferred until evaluation corpora
are supplied by dataset packages. That does not block freezing Protocol V1,
CLI, public API, or the structural production path.
