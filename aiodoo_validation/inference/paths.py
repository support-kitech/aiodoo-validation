"""Artifact load path helpers for inference."""

from __future__ import annotations

from pathlib import Path

from aiodoo_validation.domain.artifact_paths import (
    ARTIFACT_PATHS_KEY,
    ArtifactLoadPaths,
    build_artifact_paths_metadata,
)
from aiodoo_validation.domain.artifacts import ArtifactBundle
from aiodoo_validation.domain.enums import InferenceErrorCode
from aiodoo_validation.domain.inference import InferenceError

__all__ = [
    "ARTIFACT_PATHS_KEY",
    "ArtifactLoadPaths",
    "build_artifact_paths_metadata",
    "extract_load_paths",
]


def extract_load_paths(
    bundle: ArtifactBundle,
) -> tuple[ArtifactLoadPaths | None, InferenceError | None]:
    """Extract load paths stored during artifact resolution."""
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
