"""Transformation application results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.transforms.exceptions import TransformationValidationError
from aiodoo_validation.transforms.replace import ReplaceTransformation
from aiodoo_validation.transforms.snapshot import ArtifactSnapshot


@dataclass(frozen=True, slots=True)
class TransformationResult:
    """
    Outcome of applying one transformation to a snapshot.

    ``success`` is False when the transform could not be applied as intended
    (e.g. missing path, search not found). ``snapshot`` is always present:
    unchanged on failure, updated on success.
    """

    success: bool
    snapshot: ArtifactSnapshot
    original: ArtifactSnapshot
    transformation: ReplaceTransformation
    occurrence_count: int = 0
    findings: tuple[str, ...] = ()
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if self.occurrence_count < 0:
            raise TransformationValidationError("occurrence_count must be >= 0.")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata) if self.metadata is not None else {}),
        )


__all__ = ["TransformationResult"]
