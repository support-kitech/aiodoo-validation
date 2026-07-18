"""Unit tests for Planner Capability Pack (Phase 1 foundation)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiodoo_validation.capabilities.bootstrap import create_default_capability_registry
from aiodoo_validation.capabilities.planner import (
    PLANNER_PARSER_ID,
    PlannerParseError,
    PlannerRecordParser,
    get_planner_capability_pack,
)
from aiodoo_validation.capabilities.planner.specification import (
    PLANNER_CAPABILITY_ID,
    build_planner_specification,
    capability_yaml_path,
)
from aiodoo_validation.domain.capability_record import ParsedCapabilityRecord

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "capabilities" / "planner"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestPlannerSpecification:
    def test_build_matches_identity(self) -> None:
        spec = build_planner_specification()
        assert spec.id == PLANNER_CAPABILITY_ID
        assert spec.parser_id == PLANNER_PARSER_ID
        assert "replace" in spec.supported_transformation_types
        assert spec.corpus_requirements.fingerprint_required is True

    def test_capability_yaml_exists_and_aligns(self) -> None:
        text = capability_yaml_path().read_text(encoding="utf-8")
        assert "id: planner" in text
        assert "parser_id: planner_v1" in text
        assert "planner_tasks_v1" in text


class TestPlannerRegistration:
    def test_pack_registration(self) -> None:
        pack = get_planner_capability_pack()
        assert pack.parser_id == PLANNER_PARSER_ID
        assert pack.capability_id == "planner"
        assert pack.specification.parser_id == pack.parser_id
        assert isinstance(pack.parser, PlannerRecordParser)
        assert "id: planner" in pack.capability_yaml()

    def test_builtin_registry_includes_planner_and_repair(self) -> None:
        registry = create_default_capability_registry()
        assert registry.registered_ids() == (
            "approval",
            "coding",
            "conversation",
            "evaluation",
            "execution",
            "planner",
            "repair",
        )
        planner = registry.get("planner")
        assert planner.parser_id == PLANNER_PARSER_ID
        assert planner.specification.id == "planner"


class TestPlannerRecordParser:
    def setup_method(self) -> None:
        self.parser = PlannerRecordParser()

    def test_simple_generate(self) -> None:
        record = self.parser.parse(_load("simple_generate.json"))
        assert isinstance(record, ParsedCapabilityRecord)
        assert record.record_id == "planner.simple"
        assert record.capability_id == "planner"
        assert len(record.artifacts) == 2
        roles = {item.metadata.get("snapshot_role") for item in record.artifacts}
        assert roles == {"original", "expected"}
        assert record.transformations == ()
        assert record.explanation is not None

    def test_simple_replace(self) -> None:
        record = self.parser.parse(_load("simple_replace.json"))
        assert len(record.transformations) == 1
        transform = record.transformations[0]
        assert transform.transformation_type == "replace"
        assert transform.payload["search"] == "string='Old'"
        assert transform.payload["replace"] == "string='New'"

    def test_missing_fields(self) -> None:
        with pytest.raises(PlannerParseError, match="content"):
            self.parser.parse(_load("missing_fields.json"))

    def test_invalid_payload(self) -> None:
        with pytest.raises(PlannerParseError, match="search"):
            self.parser.parse(_load("invalid_payload.json"))

    def test_unsupported_schema(self) -> None:
        with pytest.raises(PlannerParseError, match="Unsupported Planner schema"):
            self.parser.parse(_load("unsupported_schema.json"))

    def test_unsupported_operation(self) -> None:
        with pytest.raises(PlannerParseError, match="unsupported operation"):
            self.parser.parse(_load("unsupported_operation.json"))

    def test_native_task(self) -> None:
        record = self.parser.parse(_load("native_task.json"))
        assert record.record_id == "native-planner-1"
        assert "active partners" in record.problem
        assert record.metadata.get("rule_id") == "planner_helper"
        roles = {item.metadata.get("snapshot_role") for item in record.artifacts}
        assert "original" in roles
        assert "expected" in roles

    def test_training_envelope(self) -> None:
        records = self.parser.parse_training_example(_load("training_envelope.json"))
        assert len(records) == 1
        assert records[0].record_id == "train-planner-1"
        assert records[0].metadata.get("instruction")
        assert any(
            item.metadata.get("snapshot_role") == "expected" for item in records[0].artifacts
        )

    def test_parse_training_via_parse_requires_single_task(self) -> None:
        payload = _load("training_envelope.json")
        record = self.parser.parse(payload)
        assert record.record_id == "train-planner-1"
