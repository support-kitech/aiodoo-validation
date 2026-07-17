"""CLI command handlers (Phase 10)."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from aiodoo_validation import __version__
from aiodoo_validation.cli.exit_codes import (
    EXIT_FAILED,
    EXIT_INVALID_REQUEST,
    exit_code_for_status,
)
from aiodoo_validation.cli.formatter import ConsoleFormatter
from aiodoo_validation.domain.enums import ExecutionTier, OdooVersion
from aiodoo_validation.domain.request import (
    SUPPORTED_PROFILES,
    SUPPORTED_PROTOCOL_MAJOR,
    ValidationRequest,
)
from aiodoo_validation.engine import PIPELINE_STAGE_ORDER, ValidationEngine
from aiodoo_validation.exceptions import InvalidRequestError
from aiodoo_validation.profiles.coding.profile import CodingProfile
from aiodoo_validation.validation_plan import ProfileCapabilities

if TYPE_CHECKING:
    from aiodoo_validation.cli.config import CliConfig


def run_validate(args: argparse.Namespace, *, config: CliConfig) -> int:
    """Build a request, run the validation engine, and print formatted output."""
    formatter = ConsoleFormatter()
    try:
        odoo_versions = _parse_odoo_versions(args.odoo_versions)
        request = ValidationRequest(
            profile_name=args.profile,
            base_model_ref=args.base_model,
            adapter_ref=args.adapter,
            merged_model_ref=args.merged_model,
            execution_tier=ExecutionTier(args.execution_tier),
            odoo_versions=odoo_versions,
            run_id=args.run_id,
        )
    except InvalidRequestError as exc:
        sys.stdout.write(formatter.format_error(str(exc)))
        return EXIT_INVALID_REQUEST
    except ValueError as exc:
        sys.stdout.write(formatter.format_error(str(exc)))
        return EXIT_INVALID_REQUEST

    engine = ValidationEngine.with_filesystem()
    try:
        result = engine.run(request)
    except Exception as exc:  # noqa: BLE001 — CLI must not crash on unexpected errors
        if config.debug or args.debug:
            raise
        sys.stdout.write(formatter.format_error(f"Validation failed unexpectedly: {exc}"))
        return EXIT_FAILED

    sys.stdout.write(formatter.format(result))
    return exit_code_for_status(result.exit_status)


def run_version(_args: argparse.Namespace, *, config: CliConfig) -> int:
    """Display repository and protocol metadata."""
    _ = config
    formatter = ConsoleFormatter()
    sys.stdout.write(
        formatter.format_version(
            repository_version=__version__,
            protocol_major=SUPPORTED_PROTOCOL_MAJOR,
            protocol_minor=0,
            supported_profiles=tuple(sorted(SUPPORTED_PROFILES)),
            supported_execution_tiers=tuple(tier.value for tier in ExecutionTier),
        )
    )
    return 0


def run_capabilities(_args: argparse.Namespace, *, config: CliConfig) -> int:
    """Display supported capabilities from static profile metadata."""
    _ = config
    formatter = ConsoleFormatter()
    profile = CodingProfile.create(
        odoo_versions=(OdooVersion.V17, OdooVersion.V18, OdooVersion.V19)
    )
    capabilities = profile.capabilities
    capability_lines = _capability_labels(capabilities)
    sys.stdout.write(
        formatter.format_capabilities(
            supported_profiles=tuple(sorted(SUPPORTED_PROFILES)),
            pipeline_stages=PIPELINE_STAGE_ORDER,
            capabilities=capability_lines,
            supported_runtimes=profile.supported_runtimes,
            supported_artifact_types=profile.supported_artifact_types,
        )
    )
    return 0


def run_help(args: argparse.Namespace, *, config: CliConfig) -> int:
    """Display CLI usage and examples."""
    formatter = ConsoleFormatter()
    program = config.program_name
    sys.stdout.write(
        formatter.format_help(
            program_name=program,
            usage=(
                f"{program} validate --profile coding --base-model ./base --adapter ./adapter\n"
                f"{program} version\n"
                f"{program} capabilities\n"
                f"{program} help"
            ),
            examples=(
                (
                    f"{program} validate --profile coding "
                    f"--base-model ./base --adapter ./adapter"
                ),
                f"{program} version",
                f"{program} capabilities",
            ),
        )
    )
    return 0


def _parse_odoo_versions(raw: str) -> tuple[int, ...]:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ValueError("odoo_versions must contain at least one version.")
    return tuple(int(part) for part in parts)


def _capability_labels(capabilities: ProfileCapabilities) -> tuple[str, ...]:
    labels: list[str] = []
    if capabilities.supports_inference:
        labels.append("supports_inference")
    if capabilities.supports_oracles:
        labels.append("supports_oracles")
    if capabilities.supports_scoring:
        labels.append("supports_scoring")
    if capabilities.supports_benchmark:
        labels.append("supports_benchmark")
    if capabilities.supports_certification:
        labels.append("supports_certification")
    if capabilities.supports_reports:
        labels.append("supports_reports")
    return tuple(labels)


def dispatch(args: argparse.Namespace, *, config: CliConfig) -> int:
    """Route parsed arguments to the selected command handler."""
    command = args.command or "help"
    if command == "validate":
        return run_validate(args, config=config)
    if command == "version":
        return run_version(args, config=config)
    if command == "capabilities":
        return run_capabilities(args, config=config)
    if command == "help":
        return run_help(args, config=config)
    sys.stdout.write(ConsoleFormatter().format_error(f"Unknown command: {command!r}"))
    return EXIT_INVALID_REQUEST
