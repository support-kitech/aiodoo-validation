"""Unit tests for the contract response parse/validate bridge."""

from __future__ import annotations

import json

import pytest
from aiodoo_contract.parsers import CapabilityParser
from aiodoo_contract.schemas.coding import CodingResponse

from aiodoo_validation.contract.parser_bridge import (
    ContractParseError,
    extract_comparable_text,
    is_contract_mapped_capability,
    parse_capability_output,
)


def test_is_contract_mapped_capability() -> None:
    assert is_contract_mapped_capability("coding") is True
    assert is_contract_mapped_capability("repair") is True
    assert is_contract_mapped_capability("evaluation") is False
    assert is_contract_mapped_capability("not-a-capability") is False


def test_parse_capability_output_success_round_trips_via_canonical_parser() -> None:
    raw = json.dumps(
        {
            "request_id": "req-1",
            "edits": [{"path": "models/sale.py", "content": "hello world"}],
        }
    )
    parsed = parse_capability_output("coding", raw)
    assert isinstance(parsed.response, CodingResponse)
    assert parsed.comparable_text == "hello world"

    # Must decode to the same field values CapabilityParser(CodingResponse)
    # would produce — no bespoke decoding logic of its own. ``created_at``
    # is excluded: each parse call stamps its own default timestamp.
    canonical = CapabilityParser(CodingResponse).parse(raw)
    assert parsed.response.model_dump(exclude={"created_at"}) == canonical.model_dump(
        exclude={"created_at"}
    )


def test_parse_capability_output_unknown_capability_fails_closed() -> None:
    with pytest.raises(ContractParseError, match="not a recognized"):
        parse_capability_output("not-a-capability", "{}")


def test_parse_capability_output_malformed_json_fails_closed() -> None:
    with pytest.raises(ContractParseError, match="did not parse"):
        parse_capability_output("coding", "this is not json")


def test_parse_capability_output_schema_mismatch_fails_closed() -> None:
    # Missing required 'edits' field.
    with pytest.raises(ContractParseError, match="did not parse"):
        parse_capability_output("coding", json.dumps({"request_id": "req-1"}))


class TestExtractComparableText:
    def test_coding(self) -> None:
        raw = json.dumps(
            {
                "request_id": "r",
                "edits": [
                    {"path": "a.py", "content": "first"},
                    {"path": "b.py", "content": "second"},
                ],
            }
        )
        parsed = parse_capability_output("coding", raw)
        assert parsed.comparable_text == "first\nsecond"

    def test_planner(self) -> None:
        raw = json.dumps(
            {
                "request_id": "r",
                "steps": [
                    {"index": 0, "description": "step one"},
                    {"index": 1, "description": "step two"},
                ],
            }
        )
        parsed = parse_capability_output("planner", raw)
        assert parsed.comparable_text == "step one\nstep two"

    def test_repair(self) -> None:
        raw = json.dumps(
            {
                "request_id": "r",
                "fix": {
                    "description": "fix it",
                    "edits": [{"path": "a.py", "content": "fixed"}],
                    "confidence": 0.9,
                },
            }
        )
        parsed = parse_capability_output("repair", raw)
        assert parsed.comparable_text == "fixed"

    def test_execution(self) -> None:
        raw = json.dumps({"request_id": "r", "status": "succeeded", "stdout": "output text"})
        parsed = parse_capability_output("execution", raw)
        assert parsed.comparable_text == "output text"

    def test_conversation(self) -> None:
        raw = json.dumps(
            {"request_id": "r", "reply": {"role": "assistant", "content": "hello there"}}
        )
        parsed = parse_capability_output("conversation", raw)
        assert parsed.comparable_text == "hello there"

    def test_approval_with_reason(self) -> None:
        raw = json.dumps({"request_id": "r", "status": "approved", "reason": "looks good"})
        parsed = parse_capability_output("approval", raw)
        assert parsed.comparable_text == "looks good"

    def test_approval_without_reason_falls_back_to_status(self) -> None:
        raw = json.dumps({"request_id": "r", "status": "rejected"})
        parsed = parse_capability_output("approval", raw)
        assert parsed.comparable_text == "rejected"

    def test_unsupported_response_type_raises(self) -> None:
        from aiodoo_contract.schemas.evaluation import EvaluationResponse

        response = EvaluationResponse(request_id="r", verdict="pass")
        with pytest.raises(ContractParseError, match="no comparable-text extractor"):
            extract_comparable_text(response)
