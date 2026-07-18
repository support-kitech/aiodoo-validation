"""Unit tests for Capability Delivery transforms package (E2)."""

from __future__ import annotations

import pytest

from aiodoo_validation.comparators import NormalizedTextComparator
from aiodoo_validation.transforms import (
    ArtifactSnapshot,
    ReplaceTransformation,
    SnapshotComparator,
    TransformationEngine,
    TransformationValidationError,
)


def _snapshot(
    contents: dict[str, str],
    *,
    snapshot_id: str = "snap-1",
) -> ArtifactSnapshot:
    return ArtifactSnapshot(snapshot_id=snapshot_id, contents=contents)


class TestArtifactSnapshot:
    def test_immutable_contents(self) -> None:
        snap = _snapshot({"a.py": "x = 1\n"})
        assert snap.get("a.py") == "x = 1\n"
        with pytest.raises(TypeError):
            snap.contents["a.py"] = "mutated"  # type: ignore[index]

    def test_equality(self) -> None:
        left = _snapshot({"a.py": "x"})
        right = _snapshot({"a.py": "x"})
        assert left == right
        assert left != _snapshot({"a.py": "y"})

    def test_rejects_empty_snapshot_id(self) -> None:
        with pytest.raises(TransformationValidationError, match="snapshot_id"):
            ArtifactSnapshot(snapshot_id="  ", contents={"a.py": "x"})

    def test_rejects_empty_path(self) -> None:
        with pytest.raises(TransformationValidationError, match="paths"):
            ArtifactSnapshot(snapshot_id="s", contents={"": "x"})

    def test_rejects_non_string_content(self) -> None:
        with pytest.raises(TransformationValidationError, match="string"):
            ArtifactSnapshot(snapshot_id="s", contents={"a.py": 1})  # type: ignore[dict-item]

    def test_with_path_content_returns_new(self) -> None:
        original = _snapshot({"a.py": "old"})
        updated = original.with_path_content("a.py", "new")
        assert original.get("a.py") == "old"
        assert updated.get("a.py") == "new"
        assert updated.snapshot_id == original.snapshot_id

    def test_require_missing_path(self) -> None:
        snap = _snapshot({"a.py": "x"})
        with pytest.raises(TransformationValidationError, match="no path"):
            snap.require("missing.py")


class TestReplaceTransformation:
    def test_rejects_empty_search(self) -> None:
        with pytest.raises(TransformationValidationError, match="search"):
            ReplaceTransformation(path="a.py", search="", replace="x")

    def test_allows_empty_replace(self) -> None:
        transform = ReplaceTransformation(path="a.py", search="todo", replace="")
        assert transform.replace == ""

    def test_rejects_blank_path(self) -> None:
        with pytest.raises(TransformationValidationError, match="path"):
            ReplaceTransformation(path="  ", search="a", replace="b")


class TestTransformationEngine:
    def setup_method(self) -> None:
        self.engine = TransformationEngine()

    def test_successful_replacement(self) -> None:
        snap = _snapshot({"mod.py": "print('hello')\n"})
        result = self.engine.apply(
            snap,
            ReplaceTransformation(path="mod.py", search="hello", replace="world"),
        )
        assert result.success
        assert result.occurrence_count == 1
        assert result.snapshot.get("mod.py") == "print('world')\n"
        assert result.original.get("mod.py") == "print('hello')\n"
        assert "replace_applied" in result.findings

    def test_search_not_found(self) -> None:
        snap = _snapshot({"mod.py": "alpha\n"})
        result = self.engine.apply(
            snap,
            ReplaceTransformation(path="mod.py", search="beta", replace="gamma"),
        )
        assert not result.success
        assert result.occurrence_count == 0
        assert result.snapshot is snap
        assert "search_not_found" in result.findings

    def test_multiple_occurrences(self) -> None:
        snap = _snapshot({"mod.py": "xx-xx-xx"})
        result = self.engine.apply(
            snap,
            ReplaceTransformation(path="mod.py", search="xx", replace="Y"),
        )
        assert result.success
        assert result.occurrence_count == 3
        assert result.snapshot.get("mod.py") == "Y-Y-Y"

    def test_empty_replacement_deletes(self) -> None:
        snap = _snapshot({"mod.py": "keep REMOVE me"})
        result = self.engine.apply(
            snap,
            ReplaceTransformation(path="mod.py", search=" REMOVE", replace=""),
        )
        assert result.success
        assert result.snapshot.get("mod.py") == "keep me"

    def test_path_not_found(self) -> None:
        snap = _snapshot({"a.py": "x"})
        result = self.engine.apply(
            snap,
            ReplaceTransformation(path="b.py", search="x", replace="y"),
        )
        assert not result.success
        assert "path_not_found" in result.findings

    def test_preserves_other_paths(self) -> None:
        snap = _snapshot({"a.py": "foo", "b.py": "bar"})
        result = self.engine.apply(
            snap,
            ReplaceTransformation(path="a.py", search="foo", replace="baz"),
        )
        assert result.snapshot.get("b.py") == "bar"
        assert result.snapshot.get("a.py") == "baz"

    def test_does_not_mutate_original(self) -> None:
        snap = _snapshot({"a.py": "one"})
        result = self.engine.apply(
            snap,
            ReplaceTransformation(path="a.py", search="one", replace="two"),
        )
        assert snap.get("a.py") == "one"
        assert result.snapshot.get("a.py") == "two"


class TestSnapshotComparator:
    def test_transformed_matches_expected(self) -> None:
        original = _snapshot({"a.py": "old"})
        transformed = _snapshot({"a.py": "new"})
        expected = _snapshot({"a.py": "new"})
        result = SnapshotComparator().compare(
            original=original,
            transformed=transformed,
            expected=expected,
        )
        assert result.passed
        assert result.path_results["a.py"].passed
        assert not result.original_vs_expected["a.py"].passed
        assert not result.original_vs_transformed["a.py"].passed

    def test_transformed_mismatch(self) -> None:
        original = _snapshot({"a.py": "old"})
        transformed = _snapshot({"a.py": "wrong"})
        expected = _snapshot({"a.py": "new"})
        result = SnapshotComparator().compare(
            original=original,
            transformed=transformed,
            expected=expected,
        )
        assert not result.passed
        assert "transformed_mismatch:a.py" in result.findings

    def test_delegates_to_normalized_comparator(self) -> None:
        original = _snapshot({"a.py": "x"})
        transformed = _snapshot({"a.py": "hello   world"})
        expected = _snapshot({"a.py": "hello world"})
        exact = SnapshotComparator().compare(
            original=original,
            transformed=transformed,
            expected=expected,
        )
        assert not exact.passed
        normalized = SnapshotComparator(comparator=NormalizedTextComparator()).compare(
            original=original,
            transformed=transformed,
            expected=expected,
        )
        assert normalized.passed

    def test_engine_then_comparator_integration(self) -> None:
        original = _snapshot({"a.py": "value = 1"})
        expected = _snapshot({"a.py": "value = 2"})
        apply_result = TransformationEngine().apply(
            original,
            ReplaceTransformation(path="a.py", search="1", replace="2"),
        )
        assert apply_result.success
        comparison = SnapshotComparator().compare(
            original=original,
            transformed=apply_result.snapshot,
            expected=expected,
        )
        assert comparison.passed

    def test_empty_snapshots_rejected(self) -> None:
        empty = ArtifactSnapshot(snapshot_id="empty", contents={})
        with pytest.raises(TransformationValidationError, match="empty"):
            SnapshotComparator().compare(
                original=empty,
                transformed=empty,
                expected=empty,
            )
