"""Unit tests for Repair Capability Pack (E4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiodoo_validation.capabilities.repair import (
    REPAIR_PARSER_ID,
    RepairParseError,
    RepairRecordParser,
    get_repair_capability_pack,
)
from aiodoo_validation.capabilities.repair.specification import (
    REPAIR_CAPABILITY_ID,
    build_repair_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_record import ParsedCapabilityRecord

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "capabilities" / "repair"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestRepairSpecification:
    def test_build_matches_identity(self) -> None:
        spec = build_repair_specification()
        assert spec.id == REPAIR_CAPABILITY_ID
        assert spec.parser_id == REPAIR_PARSER_ID
        assert "replace" in spec.supported_transformation_types
        assert spec.corpus_requirements.fingerprint_required is True

    def test_capability_yaml_exists_and_aligns(self) -> None:
        text = capability_yaml_path().read_text(encoding="utf-8")
        assert "id: repair" in text
        assert "parser_id: repair_v1" in text
        assert "supported_transformation_types:" in text
        assert "replace" in text


class TestRepairRegistration:
    def test_pack_registration(self) -> None:
        pack = get_repair_capability_pack()
        assert pack.parser_id == REPAIR_PARSER_ID
        assert pack.capability_id == "repair"
        assert pack.specification.parser_id == pack.parser_id
        assert isinstance(pack.parser, RepairRecordParser)
        assert "id: repair" in pack.capability_yaml()


class TestRepairRecordParser:
    def setup_method(self) -> None:
        self.parser = RepairRecordParser()

    def test_simple_replace(self) -> None:
        record = self.parser.parse(_load("simple_replace.json"))
        assert isinstance(record, ParsedCapabilityRecord)
        assert record.record_id == "fix.simple"
        assert record.capability_id == "repair"
        assert len(record.artifacts) == 1
        assert record.artifacts[0].path == "models/mod.py"
        assert len(record.transformations) == 1
        transform = record.transformations[0]
        assert transform.transformation_type == "replace"
        assert transform.payload["path"] == "models/mod.py"
        assert transform.payload["search"] == "self.env.cr.execute"
        assert transform.payload["replace"] == "self.env.sudo().cr.execute"
        assert record.explanation is not None

    def test_multiple_edits(self) -> None:
        record = self.parser.parse(_load("multiple_edits.json"))
        assert len(record.transformations) == 2
        assert record.transformations[0].payload["replace"] == "FOO"
        assert record.transformations[1].payload["path"] == "a.py"

    def test_noop(self) -> None:
        record = self.parser.parse(_load("noop.json"))
        assert record.transformations == ()
        assert record.artifacts[0].content == "x = 1\n"

    def test_missing_fields(self) -> None:
        with pytest.raises(RepairParseError, match="content"):
            self.parser.parse(_load("missing_fields.json"))

    def test_invalid_payload(self) -> None:
        with pytest.raises(RepairParseError, match="search"):
            self.parser.parse(_load("invalid_payload.json"))

    def test_malformed_transform(self) -> None:
        with pytest.raises(RepairParseError, match="non-empty"):
            self.parser.parse(_load("malformed_transform.json"))

    def test_unsupported_schema(self) -> None:
        with pytest.raises(RepairParseError, match="Unsupported Repair schema"):
            self.parser.parse(_load("unsupported_schema.json"))

    def test_unsupported_operation(self) -> None:
        with pytest.raises(RepairParseError, match="unsupported operation"):
            self.parser.parse(_load("unsupported_operation.json"))

    def test_native_task(self) -> None:
        record = self.parser.parse(_load("native_task.json"))
        assert record.record_id == "native-task-1"
        assert "Direct SQL" in record.problem
        assert record.metadata.get("rule_id") == "missing_sudo"
        assert record.transformations[0].payload["path"] == "models/mod.py"

    def test_training_envelope(self) -> None:
        records = self.parser.parse_training_example(_load("training_envelope.json"))
        assert len(records) == 1
        assert records[0].record_id == "train-task-1"
        assert records[0].metadata.get("instruction")
        assert records[0].transformations[0].payload["path"] == "views/view.xml"

    def test_parse_training_via_parse_requires_single_task(self) -> None:
        record = self.parser.parse(_load("training_envelope.json"))
        assert record.record_id == "train-task-1"

    def test_preserves_extra_metadata(self) -> None:
        payload = _load("simple_replace.json")
        payload["metadata"] = {"custom_flag": True, "note": "keep-me"}
        record = self.parser.parse(payload)
        assert record.metadata["custom_flag"] is True
        assert record.metadata["note"] == "keep-me"

    def test_ambiguous_path_without_op_path(self) -> None:
        payload = {
            "record_id": "ambig",
            "problem": "two files",
            "artifacts": [
                {"id": "a", "path": "a.py", "content": "a"},
                {"id": "b", "path": "b.py", "content": "b"},
            ],
            "operations": [
                {"operation": "replace", "search": "a", "replace": "A"},
            ],
        }
        with pytest.raises(RepairParseError, match="cannot be inferred"):
            self.parser.parse(payload)

    def test_no_snapshots_or_execution_side_effects(self) -> None:
        record = self.parser.parse(_load("simple_replace.json"))
        # Parser output is descriptors only — no ReplaceTransformation / snapshots.
        assert set(record.transformations[0].payload) >= {"path", "search", "replace"}
        assert "snapshot" not in record.metadata
