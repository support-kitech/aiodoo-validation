"""Unit tests for Approval Capability Pack (Phase 1 foundation)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiodoo_validation.capabilities.approval import (
    APPROVAL_PARSER_ID,
    ApprovalParseError,
    ApprovalRecordParser,
    get_approval_capability_pack,
)
from aiodoo_validation.capabilities.approval.specification import (
    APPROVAL_CAPABILITY_ID,
    build_approval_specification,
    capability_yaml_path,
)
from aiodoo_validation.capabilities.bootstrap import create_default_capability_registry
from aiodoo_validation.domain.capability_record import ParsedCapabilityRecord

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "capabilities" / "approval"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestApprovalSpecification:
    def test_build_matches_identity(self) -> None:
        spec = build_approval_specification()
        assert spec.id == APPROVAL_CAPABILITY_ID
        assert spec.parser_id == APPROVAL_PARSER_ID
        assert "replace" in spec.supported_transformation_types
        assert spec.corpus_requirements.fingerprint_required is True

    def test_capability_yaml_exists_and_aligns(self) -> None:
        text = capability_yaml_path().read_text(encoding="utf-8")
        assert "id: approval" in text
        assert "parser_id: approval_v1" in text
        assert "approval_tasks_v1" in text


class TestApprovalRegistration:
    def test_pack_registration(self) -> None:
        pack = get_approval_capability_pack()
        assert pack.parser_id == APPROVAL_PARSER_ID
        assert pack.capability_id == "approval"
        assert pack.specification.parser_id == pack.parser_id
        assert isinstance(pack.parser, ApprovalRecordParser)
        assert "id: approval" in pack.capability_yaml()

    def test_builtin_registry_includes_approval(self) -> None:
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
        approval = registry.get("approval")
        assert approval.parser_id == APPROVAL_PARSER_ID
        assert approval.specification.id == "approval"


class TestApprovalRecordParser:
    def setup_method(self) -> None:
        self.parser = ApprovalRecordParser()

    def test_simple_generate(self) -> None:
        record = self.parser.parse(_load("simple_generate.json"))
        assert isinstance(record, ParsedCapabilityRecord)
        assert record.record_id == "approval.simple"
        assert record.capability_id == "approval"
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
        with pytest.raises(ApprovalParseError, match="content"):
            self.parser.parse(_load("missing_fields.json"))

    def test_invalid_payload(self) -> None:
        with pytest.raises(ApprovalParseError, match="search"):
            self.parser.parse(_load("invalid_payload.json"))

    def test_unsupported_schema(self) -> None:
        with pytest.raises(ApprovalParseError, match="Unsupported Approval schema"):
            self.parser.parse(_load("unsupported_schema.json"))

    def test_unsupported_operation(self) -> None:
        with pytest.raises(ApprovalParseError, match="unsupported operation"):
            self.parser.parse(_load("unsupported_operation.json"))

    def test_native_task(self) -> None:
        record = self.parser.parse(_load("native_task.json"))
        assert record.record_id == "native-approval-1"
        assert "active partners" in record.problem
        assert record.metadata.get("rule_id") == "approval_helper"
        roles = {item.metadata.get("snapshot_role") for item in record.artifacts}
        assert "original" in roles
        assert "expected" in roles

    def test_training_envelope(self) -> None:
        records = self.parser.parse_training_example(_load("training_envelope.json"))
        assert len(records) == 1
        assert records[0].record_id == "train-approval-1"
        assert records[0].metadata.get("instruction")
        assert any(
            item.metadata.get("snapshot_role") == "expected" for item in records[0].artifacts
        )

    def test_parse_training_via_parse_requires_single_task(self) -> None:
        payload = _load("training_envelope.json")
        record = self.parser.parse(payload)
        assert record.record_id == "train-approval-1"
