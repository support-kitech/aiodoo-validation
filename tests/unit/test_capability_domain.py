"""Unit tests for Capability Delivery domain foundation (E0)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

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
from aiodoo_validation.domain.corpus import CorpusManifest
from aiodoo_validation.domain.enums import CorpusRole, ValidationKind
from aiodoo_validation.exceptions import DomainError


def _spec(**overrides: object) -> CapabilitySpecification:
    base: dict[str, object] = {
        "id": "repair",
        "name": "Repair",
        "description": "Independent repair capability",
        "version": "1.0.0",
        "supported_artifact_types": ("base_model", "coding_adapter"),
        "supported_transformation_types": ("replace",),
        "supported_comparator_kinds": ("exact", "json", "ast"),
        "supported_evaluation_dimensions": ("transform_correctness", "minimal_change"),
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


class TestCorpusRole:
    def test_expected_values(self) -> None:
        assert CorpusRole.TRAINING.value == "training"
        assert CorpusRole.EVALUATION.value == "evaluation"
        assert CorpusRole.SMOKE_FIXTURE.value == "smoke_fixture"
        assert len(CorpusRole) == 3


class TestCorpusManifest:
    def test_construction_and_equality(self) -> None:
        left = CorpusManifest(
            corpus_id="repair.eval.v1",
            capability_id="repair",
            role=CorpusRole.EVALUATION,
            dataset_version="v1.0.0-eval",
            fingerprint="abc123",
            source_package="aiodoo-datasets",
            denied_training_fingerprints=("train-fp",),
        )
        right = CorpusManifest(
            corpus_id="repair.eval.v1",
            capability_id="repair",
            role=CorpusRole.EVALUATION,
            dataset_version="v1.0.0-eval",
            fingerprint="abc123",
            source_package="aiodoo-datasets",
            denied_training_fingerprints=("train-fp",),
        )
        assert left == right
        assert left.role is CorpusRole.EVALUATION

    def test_immutability(self) -> None:
        manifest = CorpusManifest(
            corpus_id="c1",
            capability_id="repair",
            role=CorpusRole.SMOKE_FIXTURE,
            dataset_version="fixture",
            fingerprint="fp",
        )
        with pytest.raises(FrozenInstanceError):
            manifest.corpus_id = "other"  # type: ignore[misc]
        with pytest.raises(TypeError):
            manifest.metadata["x"] = 1  # type: ignore[index]

    def test_rejects_empty_required_fields(self) -> None:
        with pytest.raises(DomainError, match="corpus_id"):
            CorpusManifest(
                corpus_id=" ",
                capability_id="repair",
                role=CorpusRole.EVALUATION,
                dataset_version="v1",
                fingerprint="fp",
            )
        with pytest.raises(DomainError, match="fingerprint"):
            CorpusManifest(
                corpus_id="c1",
                capability_id="repair",
                role=CorpusRole.EVALUATION,
                dataset_version="v1",
                fingerprint="",
            )

    def test_rejects_duplicate_denied_fingerprints(self) -> None:
        with pytest.raises(DomainError, match="duplicates"):
            CorpusManifest(
                corpus_id="c1",
                capability_id="repair",
                role=CorpusRole.EVALUATION,
                dataset_version="v1",
                fingerprint="fp",
                denied_training_fingerprints=("a", "a"),
            )

    def test_freezes_metadata_mapping(self) -> None:
        raw = {"k": "v"}
        manifest = CorpusManifest(
            corpus_id="c1",
            capability_id="repair",
            role=CorpusRole.TRAINING,
            dataset_version="v1",
            fingerprint="fp",
            metadata=raw,
        )
        assert isinstance(manifest.metadata, MappingProxyType)
        assert manifest.metadata["k"] == "v"


class TestCapabilitySpecification:
    def test_construction(self) -> None:
        spec = _spec(supported_languages=("python", "xml"))
        assert spec.id == "repair"
        assert spec.parser_id == "repair_v1"
        assert spec.corpus_requirements.role is CorpusRole.EVALUATION
        assert "minimal_change" in spec.supported_evaluation_dimensions

    def test_immutability(self) -> None:
        spec = _spec()
        with pytest.raises(FrozenInstanceError):
            spec.name = "x"  # type: ignore[misc]

    def test_rejects_empty_id(self) -> None:
        with pytest.raises(DomainError, match="id"):
            _spec(id="")

    def test_rejects_empty_supported_lists(self) -> None:
        with pytest.raises(DomainError, match="supported_artifact_types"):
            _spec(supported_artifact_types=())

    def test_rejects_duplicate_dimensions(self) -> None:
        with pytest.raises(DomainError, match="duplicates"):
            _spec(supported_evaluation_dimensions=("a", "a"))

    def test_rejects_unknown_certification_kind(self) -> None:
        with pytest.raises(DomainError, match="unknown values"):
            _spec(supported_certification_kinds=("structural", "magic"))

    def test_corpus_requirements_must_be_evaluation(self) -> None:
        with pytest.raises(DomainError, match="evaluation"):
            CorpusRequirements(role=CorpusRole.TRAINING, fingerprint_required=True)

    def test_corpus_requirements_require_fingerprint(self) -> None:
        with pytest.raises(DomainError, match="fingerprint_required"):
            CorpusRequirements(role=CorpusRole.EVALUATION, fingerprint_required=False)

    def test_runtime_requirements_non_empty(self) -> None:
        with pytest.raises(DomainError, match="behavior_certification"):
            RuntimeRequirements(behavior_certification=" ")

    def test_equality(self) -> None:
        assert _spec() == _spec()


class TestParsedCapabilityRecord:
    def test_minimal_record(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r1",
            capability_id="repair",
            problem="Fix the issue.",
        )
        assert record.artifacts == ()
        assert record.transformations == ()
        assert record.explanation is None

    def test_full_record_equality_and_immutability(self) -> None:
        artifact = CapabilityArtifact(
            artifact_id="a1",
            path="models/x.py",
            content="print(1)\n",
            media_type="python",
        )
        transform = TransformationDescriptor(
            transformation_type="replace",
            payload={"search": "a", "replace": "b"},
        )
        left = ParsedCapabilityRecord(
            record_id="r1",
            capability_id="repair",
            problem="problem",
            artifacts=(artifact,),
            transformations=(transform,),
            explanation="because",
            tags=("security",),
        )
        right = ParsedCapabilityRecord(
            record_id="r1",
            capability_id="repair",
            problem="problem",
            artifacts=(
                CapabilityArtifact(
                    artifact_id="a1",
                    path="models/x.py",
                    content="print(1)\n",
                    media_type="python",
                ),
            ),
            transformations=(
                TransformationDescriptor(
                    transformation_type="replace",
                    payload={"search": "a", "replace": "b"},
                ),
            ),
            explanation="because",
            tags=("security",),
        )
        assert left == right
        with pytest.raises(FrozenInstanceError):
            left.problem = "other"  # type: ignore[misc]
        with pytest.raises(TypeError):
            left.transformations[0].payload["search"] = "z"  # type: ignore[index]

    def test_rejects_duplicate_artifact_ids(self) -> None:
        art = CapabilityArtifact(artifact_id="a1", path="a.py")
        with pytest.raises(DomainError, match="duplicate artifact_id"):
            ParsedCapabilityRecord(
                record_id="r1",
                capability_id="repair",
                problem="",
                artifacts=(art, CapabilityArtifact(artifact_id="a1", path="b.py")),
            )

    def test_rejects_duplicate_tags(self) -> None:
        with pytest.raises(DomainError, match="tags"):
            ParsedCapabilityRecord(
                record_id="r1",
                capability_id="repair",
                problem="p",
                tags=("a", "a"),
            )

    def test_rejects_empty_transformation_type(self) -> None:
        with pytest.raises(DomainError, match="transformation_type"):
            TransformationDescriptor(transformation_type="")

    def test_allows_empty_problem(self) -> None:
        record = ParsedCapabilityRecord(
            record_id="r1",
            capability_id="conversation",
            problem="",
        )
        assert record.problem == ""

    def test_no_repair_schema_leak_in_annotations(self) -> None:
        # Guardrail: public fields remain generic.
        fields = set(ParsedCapabilityRecord.__dataclass_fields__)
        assert "operations" not in fields
        assert "expected_outcome" not in fields
        assert "root_cause" not in fields
