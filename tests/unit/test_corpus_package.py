"""Unit tests for Capability Delivery corpus package (E1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiodoo_validation.corpus import (
    CorpusGateError,
    CorpusLoadError,
    JsonlCorpusLoader,
    corpus_manifest_from_mapping,
    evaluate_corpus_manifest,
    fingerprint_file,
    load_corpus_manifest,
    load_jsonl_records,
    require_corpus_manifest,
)
from aiodoo_validation.domain.corpus import CorpusManifest
from aiodoo_validation.domain.enums import CorpusRole

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"


class TestManifestParsing:
    def test_from_mapping_valid(self) -> None:
        manifest = corpus_manifest_from_mapping(
            {
                "corpus_id": "c1",
                "capability_id": "repair",
                "role": "evaluation",
                "dataset_version": "v1",
                "fingerprint": "abc",
            }
        )
        assert manifest.capability_id == "repair"
        assert manifest.role is CorpusRole.EVALUATION

    def test_from_mapping_rejects_unknown_role(self) -> None:
        with pytest.raises(CorpusLoadError, match="role"):
            corpus_manifest_from_mapping(
                {
                    "corpus_id": "c1",
                    "capability_id": "repair",
                    "role": "production",
                    "dataset_version": "v1",
                    "fingerprint": "abc",
                }
            )

    def test_from_mapping_rejects_missing_field(self) -> None:
        with pytest.raises(CorpusLoadError, match="corpus_id"):
            corpus_manifest_from_mapping(
                {
                    "capability_id": "repair",
                    "role": "evaluation",
                    "dataset_version": "v1",
                    "fingerprint": "abc",
                }
            )

    def test_load_manifest_file(self) -> None:
        manifest = load_corpus_manifest(FIXTURES / "valid_evaluation" / "manifest.json")
        assert manifest.corpus_id == "fixture.repair.eval"

    def test_malformed_manifest_json(self) -> None:
        with pytest.raises(CorpusLoadError, match="valid JSON"):
            load_corpus_manifest(FIXTURES / "malformed_manifest" / "manifest.json")

    def test_missing_manifest_file(self) -> None:
        with pytest.raises(CorpusLoadError, match="not found"):
            load_corpus_manifest(FIXTURES / "does_not_exist.json")


class TestJsonlLoading:
    def test_load_records(self) -> None:
        records = load_jsonl_records(FIXTURES / "valid_evaluation" / "records.jsonl")
        assert len(records) == 2
        assert records[0]["id"] == "r1"

    def test_max_records(self) -> None:
        records = load_jsonl_records(
            FIXTURES / "valid_evaluation" / "records.jsonl",
            max_records=1,
        )
        assert len(records) == 1

    def test_malformed_jsonl(self) -> None:
        with pytest.raises(CorpusLoadError, match="Malformed JSONL"):
            load_jsonl_records(FIXTURES / "malformed_jsonl" / "records.jsonl")

    def test_fingerprint_stable(self) -> None:
        path = FIXTURES / "valid_evaluation" / "records.jsonl"
        assert fingerprint_file(path) == fingerprint_file(path)


class TestGates:
    def _manifest(
        self,
        *,
        role: CorpusRole = CorpusRole.EVALUATION,
        fingerprint: str = "fp",
        denied: tuple[str, ...] = (),
    ) -> CorpusManifest:
        return CorpusManifest(
            corpus_id="c1",
            capability_id="repair",
            role=role,
            dataset_version="v1",
            fingerprint=fingerprint,
            denied_training_fingerprints=denied,
        )

    def test_evaluation_allowed(self) -> None:
        result = evaluate_corpus_manifest(self._manifest())
        assert result.allowed
        assert result.reasons == ()

    def test_training_rejected(self) -> None:
        result = evaluate_corpus_manifest(self._manifest(role=CorpusRole.TRAINING))
        assert not result.allowed
        assert any(r.startswith("role_not_evaluation") for r in result.reasons)

    def test_smoke_rejected_for_production(self) -> None:
        result = evaluate_corpus_manifest(
            self._manifest(role=CorpusRole.SMOKE_FIXTURE),
            purpose="production_behavior",
        )
        assert not result.allowed

    def test_smoke_allowed_for_test(self) -> None:
        result = evaluate_corpus_manifest(
            self._manifest(role=CorpusRole.SMOKE_FIXTURE),
            purpose="test",
        )
        assert result.allowed

    def test_fingerprint_mismatch(self) -> None:
        result = evaluate_corpus_manifest(
            self._manifest(fingerprint="aa"),
            computed_fingerprint="bb",
        )
        assert not result.allowed
        assert "fingerprint_mismatch" in result.reasons

    def test_deny_list_hit(self) -> None:
        result = evaluate_corpus_manifest(
            self._manifest(fingerprint="trainfp", denied=("trainfp",)),
        )
        assert not result.allowed
        assert "fingerprint_on_training_deny_list" in result.reasons

    def test_additional_deny_list(self) -> None:
        result = evaluate_corpus_manifest(
            self._manifest(fingerprint="x"),
            additional_denied_fingerprints=("x",),
        )
        assert not result.allowed

    def test_require_raises(self) -> None:
        with pytest.raises(CorpusGateError, match="role_not_evaluation"):
            require_corpus_manifest(self._manifest(role=CorpusRole.TRAINING))


class TestJsonlCorpusLoader:
    def test_load_valid_evaluation(self) -> None:
        loaded = JsonlCorpusLoader().load(
            FIXTURES / "valid_evaluation",
            purpose="production_behavior",
        )
        assert loaded.gate.allowed
        assert len(loaded.records) == 2
        assert loaded.computed_fingerprint == loaded.manifest.fingerprint

    def test_load_training_rejected(self) -> None:
        with pytest.raises(CorpusGateError, match="role_not_evaluation"):
            JsonlCorpusLoader().load(FIXTURES / "training_rejected")

    def test_load_smoke_for_test(self) -> None:
        loaded = JsonlCorpusLoader().load(
            FIXTURES / "smoke_fixture",
            purpose="test",
        )
        assert loaded.gate.allowed
        assert loaded.manifest.role is CorpusRole.SMOKE_FIXTURE

    def test_load_fingerprint_mismatch(self) -> None:
        with pytest.raises(CorpusGateError, match="fingerprint_mismatch"):
            JsonlCorpusLoader().load(FIXTURES / "fingerprint_mismatch")

    def test_load_deny_list_hit(self) -> None:
        with pytest.raises(CorpusGateError, match="fingerprint_on_training_deny_list"):
            JsonlCorpusLoader().load(FIXTURES / "deny_list_hit")

    def test_missing_directory(self) -> None:
        with pytest.raises(CorpusLoadError, match="does not exist"):
            JsonlCorpusLoader().load(FIXTURES / "no_such_corpus")

    def test_empty_path(self) -> None:
        with pytest.raises(CorpusLoadError, match="non-empty"):
            JsonlCorpusLoader().load("   ")

    def test_path_is_file_not_dir(self) -> None:
        with pytest.raises(CorpusLoadError, match="not a directory"):
            JsonlCorpusLoader().load(FIXTURES / "valid_evaluation" / "manifest.json")

    def test_enforce_gates_false_returns_rejected(self) -> None:
        loaded = JsonlCorpusLoader().load(
            FIXTURES / "training_rejected",
            enforce_gates=False,
        )
        assert not loaded.gate.allowed
        assert len(loaded.records) == 1

    def test_max_records(self) -> None:
        loaded = JsonlCorpusLoader().load(
            FIXTURES / "valid_evaluation",
            max_records=1,
        )
        assert len(loaded.records) == 1
        # Full-file fingerprint still matches manifest.
        assert loaded.computed_fingerprint == loaded.manifest.fingerprint

    def test_malformed_jsonl_via_loader(self) -> None:
        with pytest.raises(CorpusLoadError, match="Malformed JSONL"):
            JsonlCorpusLoader().load(FIXTURES / "malformed_jsonl")

    def test_no_capability_schema_assumptions(self) -> None:
        loaded = JsonlCorpusLoader().load(FIXTURES / "valid_evaluation")
        # Raw dicts only — loader does not require Repair fields.
        assert "instruction" not in loaded.records[0]
        assert set(loaded.records[0]) >= {"id"}

    def test_missing_records_file(self, tmp_path: Path) -> None:
        corpus = tmp_path / "no_records"
        corpus.mkdir()
        (corpus / "manifest.json").write_text(
            json.dumps(
                {
                    "corpus_id": "c",
                    "capability_id": "repair",
                    "role": "evaluation",
                    "dataset_version": "v1",
                    "fingerprint": "a" * 64,
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(CorpusLoadError, match="JSONL missing"):
            JsonlCorpusLoader().load(corpus)

    def test_jsonl_non_object_line(self, tmp_path: Path) -> None:
        path = tmp_path / "arr.jsonl"
        path.write_text("[1,2]\n", encoding="utf-8")
        with pytest.raises(CorpusLoadError, match="JSON object"):
            load_jsonl_records(path)

    def test_duplicate_deny_fingerprints_rejected(self) -> None:
        with pytest.raises(CorpusLoadError):
            corpus_manifest_from_mapping(
                {
                    "corpus_id": "c1",
                    "capability_id": "repair",
                    "role": "evaluation",
                    "dataset_version": "v1",
                    "fingerprint": "fp",
                    "denied_training_fingerprints": ["a", "a"],
                }
            )

    def test_blank_fingerprint_rejected(self) -> None:
        with pytest.raises(CorpusLoadError):
            corpus_manifest_from_mapping(
                {
                    "corpus_id": "c1",
                    "capability_id": "repair",
                    "role": "evaluation",
                    "dataset_version": "v1",
                    "fingerprint": "   ",
                }
            )
