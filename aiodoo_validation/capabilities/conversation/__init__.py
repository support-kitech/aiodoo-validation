"""Conversation Capability Pack (Capability Pack for Conversation behavioral delivery)."""

from aiodoo_validation.capabilities.conversation.exceptions import ConversationParseError
from aiodoo_validation.capabilities.conversation.parser import ConversationRecordParser
from aiodoo_validation.capabilities.conversation.registration import (
    CONVERSATION_PARSER_ID,
    ConversationCapabilityPack,
    get_conversation_capability_pack,
)
from aiodoo_validation.capabilities.conversation.specification import (
    build_conversation_specification,
)

__all__ = [
    "CONVERSATION_PARSER_ID",
    "ConversationCapabilityPack",
    "ConversationParseError",
    "ConversationRecordParser",
    "build_conversation_specification",
    "get_conversation_capability_pack",
]
