"""Artifact load path extraction for inference (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import InferenceErrorCode
from aiodoo_validation.domain.inference import InferenceError

ARTIFACT_PATHS_KEY = "_artifact_paths"


@dataclass(frozen=True, slots=True)
class ArtifactLoadPaths:
    """Resolved filesystem locations for bundle artifacts (inference-only)."""

    base_model: Path
    adapter: Path
    merged_model: Path | None = None


def extract_load_paths(
    bundle: ArtifactBundle,
) -> tuple[ArtifactLoadPaths | None, InferenceError | None]:
    """Extract inference load paths stored during filesystem artifact resolution."""
    raw = bundle.metadata.get(ARTIFACT_PATHS_KEY)
    if not isinstance(raw, dict):
        return None, InferenceError(
            code=InferenceErrorCode.MISSING_BUNDLE,
            message="Artifact bundle does not contain resolved load paths.",
            field="artifact_bundle",
        )

    base = raw.get("base_model")
    adapter = raw.get("adapter")
    if not isinstance(base, str) or not isinstance(adapter, str):
        return None, InferenceError(
            code=InferenceErrorCode.MISSING_BUNDLE,
            message="Artifact bundle load paths are incomplete.",
            field="artifact_bundle",
        )

    merged_raw = raw.get("merged_model")
    merged = Path(merged_raw) if isinstance(merged_raw, str) else None
    return ArtifactLoadPaths(
        base_model=Path(base),
        adapter=Path(adapter),
        merged_model=merged,
    ), None


def build_artifact_paths_metadata(
    *,
    base_model: str,
    adapter: str,
    merged_model: str | None = None,
) -> dict[str, str]:
    """Build inference-only path metadata for filesystem bundles."""
    paths: dict[str, str] = {
        "base_model": base_model,
        "adapter": adapter,
    }
    if merged_model is not None:
        paths["merged_model"] = merged_model
    return paths
