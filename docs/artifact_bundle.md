# Artifact Bundle

> **Historical phase name:** This document describes the **Artifact Resolution**
> workstream, which was called “Phase 2” during early Protocol V1 build-out.
> That name is **not** the Capability Delivery track (EEP E0–E8).
> See [SPECIFICATION_V1.md](SPECIFICATION_V1.md).

**Status:** Artifact resolution contract (metadata and paths; no model weight loading in this stage)

The **Artifact Bundle** is the immutable output of artifact resolution. Downstream
pipeline stages must consume this object and must **not** read raw filesystem paths
from the validation request.

## Supported artifacts

| Role | `artifact_type` | Notes |
|------|-----------------|-------|
| Base model | `base_model` | Required |
| Coding adapter | `coding_adapter` | Required; `adapter_type` must be `coding` |
| Merged model | `merged_model` | Optional placeholder for future phases |

Unsupported and rejected in Phase 2:

- Planner, repair, conversation, execution, and evaluation adapters
- Any unknown `artifact_type`

## On-disk layout (validation-side)

Each artifact directory must contain `artifact.json`:

```json
{
  "artifact_type": "base_model",
  "protocol_major": 1,
  "identifier": "my-base-model",
  "model_family": "qwen",
  "fingerprint": "placeholder:optional-expected-digest"
}
```

Coding adapter example:

```json
{
  "artifact_type": "coding_adapter",
  "protocol_major": 1,
  "identifier": "my-coding-adapter",
  "adapter_type": "coding"
}
```

Phase 2 validates metadata and paths only. No weights are loaded.

## Bundle fields

- `base_model`, `adapter` — resolved `ArtifactDescriptor` entries
- `merged_model` — optional descriptor when `merged_model_ref` is provided
- `protocol_major` / `protocol_minor` — negotiated Validation Protocol version
- `fingerprint_policy` — `strict`, `warn`, or `off`
- `bundle_digest` — deterministic digest over resolved location digests

## Descriptor exposure

`ArtifactDescriptor` exposes:

- `artifact_type`, `logical_ref`
- `location_digest` — opaque digest (placeholder in Phase 2)
- `metadata` — parsed `artifact.json` contents
- `fingerprint` — placeholder fingerprint provider output

Raw host paths are **never** attached to the bundle.

## Compatibility validation

Phase 2 validates:

1. Coding profile requires a coding adapter (`adapter_type=coding`)
2. Base model and adapter `artifact_type` values match their roles
3. Rejected adapter families are blocked explicitly
4. Duplicate resolved locations are rejected
5. `protocol_major` in metadata matches the request

## Fingerprint modes

| Mode | Behavior |
|------|----------|
| `off` | Skip expected fingerprint comparison |
| `warn` | Record warning on mismatch; continue |
| `strict` | Fail resolution on mismatch |

`strict_fingerprint_policy=True` on the request implies `strict` mode.

Phase 2 uses **placeholder** fingerprints only (`PlaceholderFingerprintProvider`).
Real content hashing is deferred to a later phase.

## Resolvers

| Implementation | Purpose |
|----------------|---------|
| `StubArtifactResolver` | CPU-only stub bundle without filesystem I/O |
| `FilesystemArtifactResolver` | Real path and metadata validation |

Both implement `ArtifactResolverPort` and are injected into `ValidationEngine`.

## Failure handling

Resolution failures return structured `ArtifactResolutionError` entries and never
raise unhandled exceptions. The engine records a failed `resolve_artifacts` stage,
sets exit status `failed`, and skips downstream stub stages.
