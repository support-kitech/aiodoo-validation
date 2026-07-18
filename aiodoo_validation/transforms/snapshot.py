"""Immutable artifact content snapshots (no I/O)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.transforms.exceptions import TransformationValidationError


def _freeze_str_mapping(value: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TransformationValidationError("contents must be a mapping of path to text.")
    frozen: dict[str, str] = {}
    for key, content in value.items():
        if not isinstance(key, str) or not key.strip():
            raise TransformationValidationError("contents keys must be non-empty paths.")
        if not isinstance(content, str):
            raise TransformationValidationError(
                f"contents[{key!r}] must be a string."
            )
        if key in frozen:
            raise TransformationValidationError(
                f"contents contains duplicate path {key!r}."
            )
        frozen[key] = content
    return MappingProxyType(frozen)


def _freeze_metadata(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise TransformationValidationError("metadata must be a mapping.")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class ArtifactSnapshot:
    """
    Immutable path-keyed content map (Spec v1.0).

    No filesystem access. Equality is structural on identity, contents, and metadata.
    """

    snapshot_id: str
    contents: Mapping[str, str]
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise TransformationValidationError("snapshot_id must be non-empty.")
        object.__setattr__(self, "contents", _freeze_str_mapping(self.contents))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(self.contents))

    def get(self, path: str) -> str | None:
        return self.contents.get(path)

    def require(self, path: str) -> str:
        if path not in self.contents:
            raise TransformationValidationError(
                f"Snapshot {self.snapshot_id!r} has no path {path!r}."
            )
        return self.contents[path]

    def with_path_content(self, path: str, content: str) -> ArtifactSnapshot:
        """Return a new snapshot with ``path`` set to ``content`` (add or replace)."""
        if not isinstance(path, str) or not path.strip():
            raise TransformationValidationError("path must be a non-empty string.")
        if not isinstance(content, str):
            raise TransformationValidationError("content must be a string.")
        updated = dict(self.contents)
        updated[path] = content
        return ArtifactSnapshot(
            snapshot_id=self.snapshot_id,
            contents=updated,
            metadata=dict(self.metadata),
        )


__all__ = ["ArtifactSnapshot"]
