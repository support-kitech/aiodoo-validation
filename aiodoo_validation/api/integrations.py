"""Generic integration helpers for ecosystem repositories (Phase 11)."""

from __future__ import annotations

from dataclasses import dataclass

from aiodoo_validation.api.metadata import get_repository_metadata
from aiodoo_validation.api.results import is_certified, is_successful
from aiodoo_validation.domain.result import ValidationRunResult

_API_IMPORT = "from aiodoo_validation.api import ValidationService, build_coding_request"


@dataclass(frozen=True, slots=True)
class TrainingIntegrationHints:
    """Hints for aiodoo-training post-export validation."""

    import_statement: str
    service_factory: str
    request_builder: str
    example_call: str


@dataclass(frozen=True, slots=True)
class ColabIntegrationHints:
    """Hints for aiodoo-colab notebook orchestration."""

    import_statement: str
    install_command: str
    example_snippet: str


@dataclass(frozen=True, slots=True)
class VscodeIntegrationHints:
    """Hints for VS Code extension integration."""

    package_import: str
    command_id: str
    settings_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelRepositoryIntegrationHints:
    """Hints for aiodoo-models promotion workflows."""

    certification_field: str
    report_field: str
    promotion_checklist: tuple[str, ...]


def training_integration_hints() -> TrainingIntegrationHints:
    """Return generic training-repository integration hints."""
    return TrainingIntegrationHints(
        import_statement=_API_IMPORT,
        service_factory="service = ValidationService.create_default()",
        request_builder=(
            "request = build_coding_request("
            "base_model_ref=export.base_model_path, adapter_ref=export.adapter_path)"
        ),
        example_call="result = service.validate(request)",
    )


def colab_integration_hints() -> ColabIntegrationHints:
    """Return generic Colab notebook integration hints."""
    metadata = get_repository_metadata()
    return ColabIntegrationHints(
        import_statement=_API_IMPORT,
        install_command="pip install -e ../aiodoo-validation",
        example_snippet=(
            "service = ValidationService.create_default()\n"
            "request = build_coding_request(base_model_ref=base_path, adapter_ref=adapter_path)\n"
            f"result = service.validate(request)  # protocol {metadata.protocol.version_label}"
        ),
    )


def vscode_integration_hints() -> VscodeIntegrationHints:
    """Return generic VS Code extension integration hints."""
    return VscodeIntegrationHints(
        package_import=_API_IMPORT,
        command_id="aiodoo.validateArtifacts",
        settings_keys=(
            "aiodoo.validation.baseModelPath",
            "aiodoo.validation.adapterPath",
            "aiodoo.validation.executionTier",
        ),
    )


def model_repository_integration_hints() -> ModelRepositoryIntegrationHints:
    """Return generic model-repository promotion hints."""
    return ModelRepositoryIntegrationHints(
        certification_field="run_context.certification_execution",
        report_field="run_context.report_execution",
        promotion_checklist=(
            "Attach ValidationRunResult to the model record.",
            "Persist report_execution for downstream renderers.",
            "Gate promotion on exit_status and certification_execution.",
            "Never re-run validation inside the model repository.",
        ),
    )


def summarize_for_promotion(result: ValidationRunResult) -> dict[str, object]:
    """Summarize a validation result for model promotion workflows."""
    return {
        "exit_status": result.exit_status.value,
        "successful": is_successful(result),
        "certified": is_certified(result),
        "run_id": result.run_context.run_id,
        "report_template_count": (
            result.run_context.report_execution.template_count
            if result.run_context.report_execution is not None
            else 0
        ),
    }
