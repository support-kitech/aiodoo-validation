"""
Stable public integration API for the AIODOO ecosystem (Phase 11).

External repositories should depend on this package only — never on internal
engine, oracle, scoring, benchmark, certification, or reporting modules.
"""

from aiodoo_validation.api.builders import (
    build_approval_request,
    build_coding_request,
    build_conversation_request,
    build_evaluation_request,
    build_execution_request,
    build_planner_request,
    parse_odoo_versions,
)
from aiodoo_validation.api.compatibility import (
    is_execution_tier_supported,
    is_odoo_version_supported,
    is_profile_supported,
    is_protocol_supported,
)
from aiodoo_validation.api.integrations import (
    colab_integration_hints,
    model_repository_integration_hints,
    summarize_for_promotion,
    training_integration_hints,
    vscode_integration_hints,
)
from aiodoo_validation.api.metadata import ProtocolInfo, RepositoryMetadata, get_repository_metadata
from aiodoo_validation.api.profiles import (
    ProfileInfo,
    capability_labels,
    get_profile_info,
    list_profiles,
)
from aiodoo_validation.api.results import (
    is_certified,
    is_successful,
    report_execution,
    stage_statuses,
)
from aiodoo_validation.api.service import ValidationService

__all__ = [
    "ProfileInfo",
    "ProtocolInfo",
    "RepositoryMetadata",
    "ValidationService",
    "build_approval_request",
    "build_coding_request",
    "build_conversation_request",
    "build_evaluation_request",
    "build_execution_request",
    "build_planner_request",
    "capability_labels",
    "colab_integration_hints",
    "get_profile_info",
    "get_repository_metadata",
    "is_certified",
    "is_execution_tier_supported",
    "is_odoo_version_supported",
    "is_profile_supported",
    "is_protocol_supported",
    "is_successful",
    "list_profiles",
    "model_repository_integration_hints",
    "parse_odoo_versions",
    "report_execution",
    "stage_statuses",
    "summarize_for_promotion",
    "training_integration_hints",
    "vscode_integration_hints",
]
