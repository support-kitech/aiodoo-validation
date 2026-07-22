"""Unit tests for the contract-to-inference-prompt bridge.

These tests specifically guard the "training and validation must generate
identical prompt text" success criterion: since both sides are required to
call ``aiodoo_contract.prompts.CapabilityPromptBuilder`` and
``aiodoo_contract.templates`` directly (never hand-format a prompt), a
prompt built by :mod:`aiodoo_validation.contract.prompt_bridge` from a given
``CapabilityRequest`` must be byte-for-byte identical to one built by calling
``aiodoo_contract`` directly with the same request — there is no local
formatting step left that could diverge.
"""

from __future__ import annotations

from aiodoo_contract.prompts import CapabilityPromptBuilder
from aiodoo_contract.schemas.coding import CodingRequest
from aiodoo_contract.templates import ChatMessage, ChatRole, get_chat_template

from aiodoo_validation.contract.adapters import project_record
from aiodoo_validation.contract.prompt_bridge import (
    DEFAULT_CHAT_TEMPLATE_NAME,
    render_capability_prompt,
    render_chat_prompt,
    render_inference_prompt,
)
from aiodoo_validation.domain.capability_record import CapabilityArtifact, ParsedCapabilityRecord


def _coding_record() -> ParsedCapabilityRecord:
    return ParsedCapabilityRecord(
        record_id="coding.record",
        capability_id="coding",
        problem="Rename the field label.",
        explanation="Update Char field label.",
        artifacts=(
            CapabilityArtifact(
                artifact_id="a1",
                path="models/sale.py",
                content="name = fields.Char(string='Old')\n",
            ),
        ),
    )


def test_render_capability_prompt_matches_direct_contract_call() -> None:
    projection = project_record(_coding_record())
    rendered = render_capability_prompt(projection)

    direct = CapabilityPromptBuilder().build_from_request(projection.request)

    assert rendered.system == direct.system
    assert rendered.user == direct.user
    assert rendered.capability == direct.capability


def test_render_chat_prompt_matches_direct_template_call() -> None:
    projection = project_record(_coding_record())
    rendered = render_capability_prompt(projection)

    prompt_text = render_chat_prompt(rendered)

    template = get_chat_template(DEFAULT_CHAT_TEMPLATE_NAME)
    messages = [
        ChatMessage(role=ChatRole.SYSTEM, content=rendered.system),
        ChatMessage(role=ChatRole.USER, content=rendered.user),
    ]
    assert prompt_text == template.render_validation(messages)
    assert prompt_text == template.render_runtime(messages)


def test_render_inference_prompt_contains_original_instruction_verbatim() -> None:
    projection = project_record(_coding_record())
    text = render_inference_prompt(projection)
    assert "Rename the field label." in text


def test_render_inference_prompt_is_deterministic() -> None:
    projection = project_record(_coding_record())
    first = render_inference_prompt(projection)
    second = render_inference_prompt(projection)
    assert first == second


def test_render_chat_prompt_omits_system_turn_when_none() -> None:
    request = CodingRequest(instruction="Do the thing.")
    rendered = CapabilityPromptBuilder().build_from_request(request)
    rendered_without_system = rendered.model_copy(update={"system": None})
    text = render_chat_prompt(rendered_without_system)
    assert "System:" not in text
    assert "Do the thing." in text
