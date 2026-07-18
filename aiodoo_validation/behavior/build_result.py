"""Immutable result of assembling a behavioral case from a capability record."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.domain.behavior import BehaviorCase
from aiodoo_validation.transforms.replace import ReplaceTransformation
from aiodoo_validation.transforms.snapshot import ArtifactSnapshot


@dataclass(frozen=True, slots=True)
class BehaviorCaseBuildResult:
    """
    Assembled behavior case plus transform-ready snapshots.

    ``case`` is the existing domain ``BehaviorCase`` used by BehaviorRunner.
    Snapshots and mapped transformations are prepared for later consumers
    (TransformationEngine / oracles) — they are not applied here.
    """

    case: BehaviorCase
    original_snapshot: ArtifactSnapshot
    expected_snapshot: ArtifactSnapshot
    transformations: tuple[ReplaceTransformation, ...] = ()
    record_id: str = ""
    capability_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.case, BehaviorCase):
            raise TypeError("case must be a BehaviorCase.")
        if not isinstance(self.original_snapshot, ArtifactSnapshot):
            raise TypeError("original_snapshot must be an ArtifactSnapshot.")
        if not isinstance(self.expected_snapshot, ArtifactSnapshot):
            raise TypeError("expected_snapshot must be an ArtifactSnapshot.")
        transforms = tuple(self.transformations)
        if not all(isinstance(item, ReplaceTransformation) for item in transforms):
            raise TypeError("transformations must contain ReplaceTransformation values only.")
        object.__setattr__(self, "transformations", transforms)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata) if self.metadata is not None else {}),
        )


__all__ = ["BehaviorCaseBuildResult"]
