"""Generic TransformationEngine — replace-only, deterministic."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.transforms.replace import ReplaceTransformation
from aiodoo_validation.transforms.result import TransformationResult
from aiodoo_validation.transforms.snapshot import ArtifactSnapshot


@dataclass(frozen=True, slots=True)
class TransformationEngine:
    """
    Apply literal replace transformations to artifact snapshots.

    No capability schema knowledge. No scoring. No certification.
    Missing search targets produce findings (fail-soft result), not raises.
    Missing paths produce findings. Empty search is rejected at construction.
    """

    def apply(
        self,
        snapshot: ArtifactSnapshot,
        transformation: ReplaceTransformation,
    ) -> TransformationResult:
        if not isinstance(snapshot, ArtifactSnapshot):
            raise TypeError("snapshot must be an ArtifactSnapshot.")
        if not isinstance(transformation, ReplaceTransformation):
            raise TypeError("transformation must be a ReplaceTransformation.")

        path = transformation.path
        if path not in snapshot.contents:
            return TransformationResult(
                success=False,
                snapshot=snapshot,
                original=snapshot,
                transformation=transformation,
                occurrence_count=0,
                findings=("path_not_found",),
                message=f"Path {path!r} is not present in snapshot {snapshot.snapshot_id!r}.",
                metadata={"path": path},
            )

        content = snapshot.contents[path]
        search = transformation.search
        count = content.count(search)
        if count == 0:
            return TransformationResult(
                success=False,
                snapshot=snapshot,
                original=snapshot,
                transformation=transformation,
                occurrence_count=0,
                findings=("search_not_found",),
                message=(
                    f"Search text not found in snapshot {snapshot.snapshot_id!r} path {path!r}."
                ),
                metadata={"path": path, "search_length": len(search)},
            )

        updated_content = content.replace(search, transformation.replace)
        updated = snapshot.with_path_content(path, updated_content)
        return TransformationResult(
            success=True,
            snapshot=updated,
            original=snapshot,
            transformation=transformation,
            occurrence_count=count,
            findings=("replace_applied",),
            message=f"Replaced {count} occurrence(s) in path {path!r}.",
            metadata={
                "path": path,
                "search_length": len(search),
                "replace_length": len(transformation.replace),
            },
        )


__all__ = ["TransformationEngine"]
