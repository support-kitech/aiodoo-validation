"""CLI command handlers (Phase 10)."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from aiodoo_validation.api import (
    ValidationService,
    build_coding_request,
    capability_labels,
    get_profile_info,
    get_repository_metadata,
    list_profiles,
    parse_odoo_versions,
)
from aiodoo_validation.cli.exit_codes import (
    EXIT_FAILED,
    EXIT_INVALID_REQUEST,
    exit_code_for_status,
)
from aiodoo_validation.cli.formatter import ConsoleFormatter
from aiodoo_validation.domain.enums import ExecutionTier
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.exceptions import InvalidRequestError

if TYPE_CHECKING:
    from aiodoo_validation.cli.config import CliConfig


def run_validate(args: argparse.Namespace, *, config: CliConfig) -> int:
    """Build a request, run validation, and print formatted output."""
    formatter = ConsoleFormatter()
    try:
        request = _build_request(args)
    except InvalidRequestError as exc:
        sys.stdout.write(formatter.format_error(str(exc)))
        return EXIT_INVALID_REQUEST
    except ValueError as exc:
        sys.stdout.write(formatter.format_error(str(exc)))
        return EXIT_INVALID_REQUEST

    service = ValidationService.create_default()
    try:
        result = service.validate(request)
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
    metadata = get_repository_metadata()
    formatter = ConsoleFormatter()
    sys.stdout.write(
        formatter.format_version(
            repository_version=metadata.repository_version,
            protocol_major=metadata.protocol.major,
            protocol_minor=metadata.protocol.minor,
            supported_profiles=metadata.supported_profiles,
            supported_execution_tiers=metadata.supported_execution_tiers,
        )
    )
    return 0


def run_capabilities(_args: argparse.Namespace, *, config: CliConfig) -> int:
    """Display supported capabilities from static profile metadata."""
    _ = config
    formatter = ConsoleFormatter()
    profile_name = list_profiles()[0]
    profile = get_profile_info(profile_name)
    sys.stdout.write(
        formatter.format_capabilities(
            supported_profiles=list_profiles(),
            pipeline_stages=profile.pipeline_stages,
            capabilities=capability_labels(profile.capabilities),
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
                (f"{program} validate --profile coding --base-model ./base --adapter ./adapter"),
                f"{program} version",
                f"{program} capabilities",
            ),
        )
    )
    return 0


def _build_request(args: argparse.Namespace) -> ValidationRequest:
    odoo_versions = parse_odoo_versions(args.odoo_versions)
    if args.profile == "coding":
        return build_coding_request(
            base_model_ref=args.base_model,
            adapter_ref=args.adapter,
            merged_model_ref=args.merged_model,
            execution_tier=args.execution_tier,
            odoo_versions=odoo_versions,
            run_id=args.run_id,
        )
    return ValidationRequest(
        profile_name=args.profile,
        base_model_ref=args.base_model,
        adapter_ref=args.adapter,
        merged_model_ref=args.merged_model,
        execution_tier=ExecutionTier(args.execution_tier),
        odoo_versions=odoo_versions,
        run_id=args.run_id,
    )


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
