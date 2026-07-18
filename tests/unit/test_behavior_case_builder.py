"""Unit tests for BehaviorCaseBuilder (Capability Delivery E3)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from aiodoo_validation.behavior import (
    BehaviorCaseBuilder,
    BehaviorCaseBuildError,
    descriptor_to_replace_transformation,
)
from aiodoo_validation.domain.behavior import BehaviorCase
from aiodoo_validation.domain.capability_record import (
    CapabilityArtifact,
    ParsedCapabilityRecord,
    TransformationDescriptor,
)
from aiodoo_validation.domain.capability_spec import (
    CapabilitySpecification,
    CorpusRequirements,
    RuntimeRequirements,
)
from aiodoo_validation.domain.enums import ComparatorKind, CorpusRole, ValidationKind


def _spec(**overrides: object) -> CapabilitySpecification:
    base: dict[str, object] = {
        "id": "repair",
        "name": "Repair",
        "description": "Independent repair capability",
        "version": "1.0.0",
        "supported_artifact_types": ("base_model", "coding_adapter"),
        "supported_transformation_types": ("replace",),
        "supported_comparator_kinds": ("exact", "ast"),
        "supported_evaluation_dimensions": ("transform_correctness",),
        "supported_certification_kinds": (
            ValidationKind.STRUCTURAL.value,
            ValidationKind.BEHAVIORAL.value,
        ),
        "corpus_schema_id": "repair_tasks_v1",
        "corpus_requirements": CorpusRequirements(
            role=CorpusRole.EVALUATION,
            fingerprint_required=True,
        ),
        "default_scoring_policy_ref": "scoring_policy.yaml",
        "default_certification_policy_ref": "certification_defaults.yaml",
        "runtime_requirements": RuntimeRequirements(
            behavior_certification="real_inference",
        ),
        "parser_id": "repair_v1",
    }
    base.update(overrides)
    return CapabilitySpecification(**base)  # type: ignore[arg-type]


def _replace(
    *,
    path: str = "mod.py",
    search: str = "old",
    replace: str = "new",
) -> TransformationDescriptor:
    return TransformationDescriptor(
        transformation_type="replace",
        payload={"path": path, "search": search, "replace": replace},
    )


class TestDescriptorMapping:
    def test_maps_replace_descriptor(self) -> None:
        transform = descriptor_to_replace_transformation(_replace())
        assert transform.path == "mod.py"
        assert transform.search == "old"
        assert transform.replace == "new"

    def test_rejects_unsupported_type(self) -> None:
        with pytest.raises(BehaviorCaseBuildError, match="Unsupported transformation"):
            descriptor_to_replace_transformation(
                TransformationDescriptor(transformation_type="patch", payload={})
            )

    def test_rejects_missing_payload_fields(self) -> None:
        with pytest.raises(BehaviorCaseBuildError, match="missing required field"):
            descriptor_to_replace_transformation(
                TransformationDescriptor(
                    transformation_type="replace",
                    payload={"path": "a.py", "search": "x"},
                )
            )

    def test_rejects_empty_search(self) -> None:
        with pytest.raises(BehaviorCaseBuildError, match="search"):
            descriptor_to_replace_transformation(
                _replace(search=""),
            )


class TestBehaviorCaseBuilder:
    def setup_method(self) -> None:
        self.builder = BehaviorCaseBuilder()
        self.spec = _spec()

    def test_minimal_record(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r1",
            capability_id="repair",
            problem="Fix the bug",
            artifacts=(
                CapabilityArtifact(
                    artifact_id="a1",
                    path="mod.py",
                    content="x = 1\n",
                ),
            ),
        )
        result = self.builder.build(record, self.spec)
        assert isinstance(result.case, BehaviorCase)
        assert result.case.case_id == "r1"
        assert result.case.prompt.text == "Fix the bug"
        assert result.case.comparator_kind is ComparatorKind.EXACT
        assert result.original_snapshot.get("mod.py") == "x = 1\n"
        assert result.expected_snapshot.get("mod.py") == "x = 1\n"
        assert result.transformations == ()
        assert result.capability_id == "repair"

    def test_multiple_artifacts(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r2",
            capability_id="repair",
            problem="multi",
            artifacts=(
                CapabilityArtifact(artifact_id="a1", path="a.py", content="A"),
                CapabilityArtifact(artifact_id="b1", path="b.py", content="B"),
            ),
        )
        result = self.builder.build(record, self.spec)
        assert set(result.original_snapshot.contents) == {"a.py", "b.py"}

    def test_multiple_transformations(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r3",
            capability_id="repair",
            problem="edit",
            artifacts=(
                CapabilityArtifact(
                    artifact_id="a1",
                    path="mod.py",
                    content="foo bar baz",
                ),
            ),
            transformations=(
                _replace(search="foo", replace="FOO"),
                _replace(search="baz", replace="BAZ"),
            ),
        )
        result = self.builder.build(record, self.spec)
        assert len(result.transformations) == 2
        assert result.transformations[0].replace == "FOO"
        assert result.transformations[1].replace == "BAZ"
        # Builder must not apply transforms.
        assert result.original_snapshot.get("mod.py") == "foo bar baz"
        assert result.expected_snapshot.get("mod.py") == "foo bar baz"

    def test_no_transformations(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r4",
            capability_id="repair",
            problem="prompt only is ok with artifacts",
            artifacts=(CapabilityArtifact(artifact_id="a1", path="x.py", content=""),),
        )
        result = self.builder.build(record, self.spec)
        assert result.transformations == ()

    def test_expected_role_artifacts(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r5",
            capability_id="repair",
            problem="with gold",
            artifacts=(
                CapabilityArtifact(
                    artifact_id="in",
                    path="mod.py",
                    content="broken",
                ),
                CapabilityArtifact(
                    artifact_id="out",
                    path="mod.py",
                    content="fixed",
                    metadata={"snapshot_role": "expected"},
                ),
            ),
        )
        result = self.builder.build(record, self.spec)
        assert result.original_snapshot.get("mod.py") == "broken"
        assert result.expected_snapshot.get("mod.py") == "fixed"
        assert result.case.expected.text == "fixed"

    def test_capability_id_mismatch(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r6",
            capability_id="linux",
            problem="nope",
            artifacts=(CapabilityArtifact(artifact_id="a1", path="a.py", content="x"),),
        )
        with pytest.raises(BehaviorCaseBuildError, match="does not match"):
            self.builder.build(record, self.spec)

    def test_missing_problem_and_artifacts(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r7",
            capability_id="repair",
            problem="   ",
            artifacts=(),
        )
        with pytest.raises(BehaviorCaseBuildError, match="problem"):
            self.builder.build(record, self.spec)

    def test_transformations_without_original_artifacts(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r8",
            capability_id="repair",
            problem="need files",
            artifacts=(),
            transformations=(_replace(),),
        )
        with pytest.raises(BehaviorCaseBuildError, match="no original artifacts"):
            self.builder.build(record, self.spec)

    def test_transform_path_missing_from_snapshot(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r9",
            capability_id="repair",
            problem="bad path",
            artifacts=(CapabilityArtifact(artifact_id="a1", path="a.py", content="x"),),
            transformations=(_replace(path="missing.py"),),
        )
        with pytest.raises(BehaviorCaseBuildError, match="absent from the original"):
            self.builder.build(record, self.spec)

    def test_unsupported_transform_type_vs_spec(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r10",
            capability_id="repair",
            problem="patch",
            artifacts=(CapabilityArtifact(artifact_id="a1", path="a.py", content="x"),),
            transformations=(TransformationDescriptor(transformation_type="yaml", payload={}),),
        )
        with pytest.raises(BehaviorCaseBuildError, match="not declared"):
            self.builder.build(record, self.spec)

    def test_duplicate_path_same_role(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r11",
            capability_id="repair",
            problem="dup",
            artifacts=(
                CapabilityArtifact(artifact_id="a1", path="a.py", content="1"),
                CapabilityArtifact(artifact_id="a2", path="a.py", content="2"),
            ),
        )
        with pytest.raises(BehaviorCaseBuildError, match="Duplicate artifact path"):
            self.builder.build(record, self.spec)

    def test_invalid_snapshot_role(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r12",
            capability_id="repair",
            problem="role",
            artifacts=(
                CapabilityArtifact(
                    artifact_id="a1",
                    path="a.py",
                    content="x",
                    metadata={"snapshot_role": "gold"},
                ),
            ),
        )
        with pytest.raises(BehaviorCaseBuildError, match="unsupported snapshot_role"):
            self.builder.build(record, self.spec)

    def test_comparator_override(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r13",
            capability_id="repair",
            problem="ast",
            artifacts=(CapabilityArtifact(artifact_id="a1", path="a.py", content="x=1"),),
            metadata={"comparator_kind": "ast"},
        )
        result = self.builder.build(record, self.spec)
        assert result.case.comparator_kind is ComparatorKind.AST

    def test_comparator_not_in_spec(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r14",
            capability_id="repair",
            problem="json",
            artifacts=(CapabilityArtifact(artifact_id="a1", path="a.py", content="{}"),),
            metadata={"comparator_kind": "json"},
        )
        with pytest.raises(BehaviorCaseBuildError, match="not declared"):
            self.builder.build(record, self.spec)

    def test_build_many(self) -> None:
        records = (
            ParsedCapabilityRecord(
                record_id="m1",
                capability_id="repair",
                problem="one",
                artifacts=(CapabilityArtifact(artifact_id="a1", path="a.py", content="1"),),
            ),
            ParsedCapabilityRecord(
                record_id="m2",
                capability_id="repair",
                problem="two",
                artifacts=(CapabilityArtifact(artifact_id="b1", path="b.py", content="2"),),
            ),
        )
        results = self.builder.build_many(records, self.spec)
        assert len(results) == 2
        assert [item.case.case_id for item in results] == ["m1", "m2"]

    def test_immutability(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r15",
            capability_id="repair",
            problem="imm",
            artifacts=(CapabilityArtifact(artifact_id="a1", path="a.py", content="x"),),
            transformations=(_replace(path="a.py"),),
        )
        result = self.builder.build(record, self.spec)
        with pytest.raises(FrozenInstanceError):
            result.record_id = "other"  # type: ignore[misc]
        with pytest.raises(TypeError):
            result.original_snapshot.contents["a.py"] = "mut"  # type: ignore[index]

    def test_problem_only_without_artifacts(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r16",
            capability_id="repair",
            problem="Explain the issue",
            artifacts=(),
        )
        result = self.builder.build(record, self.spec)
        assert result.original_snapshot.contents == {}
        assert result.case.prompt.text == "Explain the issue"
