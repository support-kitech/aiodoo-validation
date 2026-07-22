"""Bridge a contract projection into a chat-template-rendered inference prompt.

This is the only place in aiodoo-validation that turns a capability request
into prompt text handed to an inference runner. It delegates every
formatting decision to ``aiodoo_contract.prompts.CapabilityPromptBuilder``
(ADR-0003) and every chat-turn-to-text rendering decision to
``aiodoo_contract.templates`` (ADR-0004) — validation must not hand-assemble
instruction/context strings or role-prefixed turns itself. Doing so is what
makes it possible to assert that training and validation render byte-for-byte
identical prompt text for the same contract request.
"""

from __future__ import annotations

from aiodoo_contract.prompts import CapabilityPromptBuilder, RenderedPrompt
from aiodoo_contract.templates import ChatMessage, ChatRole, get_chat_template

from aiodoo_validation.contract.adapters import ContractProjection

__all__ = [
    "DEFAULT_CHAT_TEMPLATE_NAME",
    "render_capability_prompt",
    "render_chat_prompt",
    "render_inference_prompt",
]

#: The chat template behavioral inference renders through when a profile
#: does not declare a model-family-specific template. ``"generic"`` is a
#: plain-text, role-prefixed rendering with no special tokens — safe for
#: any runtime (including the stub/scripted runners used in tests).
DEFAULT_CHAT_TEMPLATE_NAME = "generic"

_PROMPT_BUILDER = CapabilityPromptBuilder()


def render_capability_prompt(projection: ContractProjection) -> RenderedPrompt:
    """Render ``projection.request`` via the canonical Capability Prompt Builder.

    This is the single call site every capability's prompt construction
    goes through — see :class:`aiodoo_contract.prompts.CapabilityPromptBuilder`.
    """
    return _PROMPT_BUILDER.build_from_request(projection.request)


def render_chat_prompt(
    rendered: RenderedPrompt,
    *,
    chat_template_name: str = DEFAULT_CHAT_TEMPLATE_NAME,
) -> str:
    """Render ``rendered`` into model-ready text via ``aiodoo_contract.templates``.

    Uses :meth:`~aiodoo_contract.templates.base.BaseChatTemplate.render_validation`
    — the same method name the ADR reserves specifically for
    behavioral-certification inference, and which is guaranteed identical to
    :meth:`~aiodoo_contract.templates.base.BaseChatTemplate.render_runtime`
    so a model certified against this rendering is certified against what
    runtime will actually send it.
    """
    template = get_chat_template(chat_template_name)
    messages: list[ChatMessage] = []
    if rendered.system:
        messages.append(ChatMessage(role=ChatRole.SYSTEM, content=rendered.system))
    messages.append(ChatMessage(role=ChatRole.USER, content=rendered.user))
    return template.render_validation(messages)


def render_inference_prompt(
    projection: ContractProjection,
    *,
    chat_template_name: str = DEFAULT_CHAT_TEMPLATE_NAME,
) -> str:
    """Render ``projection`` straight through to chat-templated inference text.

    Composes :func:`render_capability_prompt` and :func:`render_chat_prompt`
    — the single end-to-end call
    :class:`~aiodoo_validation.behavior.capability_pipeline.CapabilityBehaviorPipeline`
    uses to produce the exact text handed to ``InferenceRunnerPort.generate``.
    """
    rendered = render_capability_prompt(projection)
    return render_chat_prompt(rendered, chat_template_name=chat_template_name)
