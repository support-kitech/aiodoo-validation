"""Artifact load path metadata (shared by resolution and inference)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ARTIFACT_PATHS_KEY = "_artifact_paths"


@dataclass(frozen=True, slots=True)
class ArtifactLoadPaths:
    """Resolved filesystem locations for bundle artifacts (inference-only consumption)."""

    base_model: Path
    adapter: Path
    merged_model: Path | None = None


def build_artifact_paths_metadata(
    *,
    base_model: str,
    adapter: str,
    merged_model: str | None = None,
) -> dict[str, str]:
    """Build inference-only path metadata stored on resolved bundles."""
    paths: dict[str, str] = {
        "base_model": base_model,
        "adapter": adapter,
    }
    if merged_model is not None:
        paths["merged_model"] = merged_model
    return paths
