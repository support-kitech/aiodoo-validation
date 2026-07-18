"""SnapshotComparator — delegates text comparison to the comparator framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from aiodoo_validation.comparators import Comparator, ExactMatchComparator
from aiodoo_validation.domain.behavior import ExpectedOutput, GeneratedOutput
from aiodoo_validation.domain.comparator import ComparatorResult
from aiodoo_validation.transforms.exceptions import TransformationValidationError
from aiodoo_validation.transforms.snapshot import ArtifactSnapshot


@dataclass(frozen=True, slots=True)
class SnapshotComparisonResult:
    """Aggregated comparison of original / transformed / expected snapshots."""

    passed: bool
    path_results: Mapping[str, ComparatorResult]
    original_vs_expected: Mapping[str, ComparatorResult]
    original_vs_transformed: Mapping[str, ComparatorResult]
    findings: tuple[str, ...] = ()
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "path_results", MappingProxyType(dict(self.path_results))
        )
        object.__setattr__(
            self,
            "original_vs_expected",
            MappingProxyType(dict(self.original_vs_expected)),
        )
        object.__setattr__(
            self,
            "original_vs_transformed",
            MappingProxyType(dict(self.original_vs_transformed)),
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata) if self.metadata is not None else {}),
        )


@dataclass(frozen=True, slots=True)
class SnapshotComparator:
    """
    Compare snapshots by delegating per-path text comparison to a ``Comparator``.

    Does not reimplement equality / AST / JSON logic. Default delegate is
    ``ExactMatchComparator``.
    """

    comparator: Comparator = field(default_factory=ExactMatchComparator)

    def compare(
        self,
        *,
        original: ArtifactSnapshot,
        transformed: ArtifactSnapshot,
        expected: ArtifactSnapshot,
    ) -> SnapshotComparisonResult:
        if not isinstance(original, ArtifactSnapshot):
            raise TypeError("original must be an ArtifactSnapshot.")
        if not isinstance(transformed, ArtifactSnapshot):
            raise TypeError("transformed must be an ArtifactSnapshot.")
        if not isinstance(expected, ArtifactSnapshot):
            raise TypeError("expected must be an ArtifactSnapshot.")

        paths = sorted(
            set(original.contents)
            | set(transformed.contents)
            | set(expected.contents)
        )
        if not paths:
            raise TransformationValidationError(
                "Cannot compare empty snapshots (no paths)."
            )

        findings: list[str] = []
        path_results: dict[str, ComparatorResult] = {}
        original_vs_expected: dict[str, ComparatorResult] = {}
        original_vs_transformed: dict[str, ComparatorResult] = {}

        for path in paths:
            if path not in expected.contents:
                findings.append(f"expected_path_missing:{path}")
            if path not in transformed.contents:
                findings.append(f"transformed_path_missing:{path}")
            if path not in original.contents:
                findings.append(f"original_path_missing:{path}")

            expected_text = expected.contents.get(path, "")
            transformed_text = transformed.contents.get(path, "")
            original_text = original.contents.get(path, "")

            path_results[path] = self.comparator.compare(
                expected=ExpectedOutput(text=expected_text),
                generated=GeneratedOutput(text=transformed_text),
            )
            original_vs_expected[path] = self.comparator.compare(
                expected=ExpectedOutput(text=expected_text),
                generated=GeneratedOutput(text=original_text),
            )
            original_vs_transformed[path] = self.comparator.compare(
                expected=ExpectedOutput(text=original_text),
                generated=GeneratedOutput(text=transformed_text),
            )

            if not path_results[path].passed:
                findings.append(f"transformed_mismatch:{path}")

        # Primary verdict: every expected path present in transformed and matching.
        expected_paths = set(expected.contents)
        passed = bool(expected_paths) and all(
            path in transformed.contents and path_results[path].passed
            for path in expected_paths
        )
        if not expected_paths:
            findings.append("expected_empty")
            passed = False

        message = (
            "Transformed snapshot matches expected."
            if passed
            else "Transformed snapshot does not match expected."
        )
        return SnapshotComparisonResult(
            passed=passed,
            path_results=path_results,
            original_vs_expected=original_vs_expected,
            original_vs_transformed=original_vs_transformed,
            findings=tuple(findings),
            message=message,
            metadata={
                "path_count": len(paths),
                "expected_path_count": len(expected_paths),
                "comparator_id": self.comparator.metadata.comparator_id,
            },
        )


__all__ = [
    "SnapshotComparator",
    "SnapshotComparisonResult",
]
