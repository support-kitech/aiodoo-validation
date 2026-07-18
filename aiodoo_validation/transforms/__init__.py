"""Generic replace-only transformation infrastructure (Capability Delivery E2)."""

from aiodoo_validation.transforms.comparator import (
    SnapshotComparator,
    SnapshotComparisonResult,
)
from aiodoo_validation.transforms.engine import TransformationEngine
from aiodoo_validation.transforms.exceptions import (
    TransformationError,
    TransformationValidationError,
)
from aiodoo_validation.transforms.replace import ReplaceTransformation
from aiodoo_validation.transforms.result import TransformationResult
from aiodoo_validation.transforms.snapshot import ArtifactSnapshot

__all__ = [
    "ArtifactSnapshot",
    "ReplaceTransformation",
    "SnapshotComparator",
    "SnapshotComparisonResult",
    "TransformationEngine",
    "TransformationError",
    "TransformationResult",
    "TransformationValidationError",
]
