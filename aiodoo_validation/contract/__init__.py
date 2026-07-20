"""Bridge between aiodoo-validation's internal domain and ``aiodoo_contract``.

This package is validation's consumer-side equivalent of aiodoo-training's
``aiodoo_training/contract`` package and aiodoo-datasets'
``generators/common/contract`` package: it owns nothing that
``aiodoo_contract`` already defines (no schemas, no prompt builder, no chat
templates, no parsers, no validators). It only:

1. **Projects** (:mod:`aiodoo_validation.contract.adapters`) a
   :class:`~aiodoo_validation.domain.capability_record.ParsedCapabilityRecord`
   — validation's own, capability-agnostic parse of a corpus record — onto
   the canonical ``aiodoo_contract.schemas`` request/response shape for its
   capability.
2. **Bridges** (:mod:`aiodoo_validation.contract.prompt_bridge`) that
   projection into a rendered, chat-templated prompt via
   ``aiodoo_contract.prompts.CapabilityPromptBuilder`` and
   ``aiodoo_contract.templates``.
3. **Bridges** (:mod:`aiodoo_validation.contract.parser_bridge`) raw model
   output produced during behavioral inference back into a canonical
   ``aiodoo_contract.schemas`` response via ``aiodoo_contract.parsers`` and
   ``aiodoo_contract.validators``.
4. **Gates** (:mod:`aiodoo_validation.contract.version_check`) certification
   on contract version compatibility via ``aiodoo_contract.version``.

Why this logic exists here and not just imported from aiodoo-training or
aiodoo-datasets: there is no validation → datasets / validation → training
Python dependency edge (see ``docs/adr/0008-dependency-graph.md`` in
aiodoo-contract). Validation consumes corpora as on-disk JSONL/native
records, not as a Python import of an upstream repository's internals, so it
re-implements this narrow projection/bridging step against the one
canonical target (:mod:`aiodoo_contract`) rather than redefining the target
itself. See ``CONTRACT_ADOPTION.md`` for the full rationale.
"""

from aiodoo_validation.contract.adapters import (
    SUPPORTED_CAPABILITIES,
    ContractAdapterError,
    ContractProjection,
    project_record,
)
from aiodoo_validation.contract.parser_bridge import (
    ContractParseError,
    ParsedContractOutput,
    extract_comparable_text,
    is_contract_mapped_capability,
    parse_capability_output,
)
from aiodoo_validation.contract.prompt_bridge import (
    DEFAULT_CHAT_TEMPLATE_NAME,
    render_capability_prompt,
    render_chat_prompt,
    render_inference_prompt,
)
from aiodoo_validation.contract.version_check import (
    VALIDATION_CONTRACT_VERSION,
    ContractVersionError,
    ensure_contract_compatible,
)

__all__ = [
    "DEFAULT_CHAT_TEMPLATE_NAME",
    "SUPPORTED_CAPABILITIES",
    "VALIDATION_CONTRACT_VERSION",
    "ContractAdapterError",
    "ContractParseError",
    "ContractProjection",
    "ContractVersionError",
    "ParsedContractOutput",
    "ensure_contract_compatible",
    "extract_comparable_text",
    "is_contract_mapped_capability",
    "parse_capability_output",
    "project_record",
    "render_capability_prompt",
    "render_chat_prompt",
    "render_inference_prompt",
]
