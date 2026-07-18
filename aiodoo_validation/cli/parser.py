"""Argument parser for the production CLI (Phase 10)."""

from __future__ import annotations

import argparse

from aiodoo_validation.cli.config import CliConfig


def build_parser(config: CliConfig) -> argparse.ArgumentParser:
    """Build the top-level CLI parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog=config.program_name,
        description="AIODOO Validation — Canonical Evaluation & Certification Framework",
        add_help=False,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show tracebacks for unexpected errors.",
    )

    subparsers = parser.add_subparsers(dest="command", required=False)

    validate = subparsers.add_parser(
        "validate",
        help="Run a validation lifecycle",
        description="Execute the Validation Protocol V1 lifecycle for trained artifacts.",
    )
    validate.add_argument(
        "--profile",
        default="coding",
        help="Validation profile name (default: coding).",
    )
    validate.add_argument(
        "--base-model",
        required=True,
        dest="base_model",
        help="Path or logical reference to the base model artifact.",
    )
    validate.add_argument(
        "--adapter",
        required=True,
        help="Path or logical reference to the adapter artifact.",
    )
    validate.add_argument(
        "--merged-model",
        dest="merged_model",
        default=None,
        help="Optional path or reference to a merged model artifact.",
    )
    validate.add_argument(
        "--execution-tier",
        dest="execution_tier",
        default="standard",
        choices=("smoke", "standard", "full", "prod"),
        help=("Validation execution tier (default: standard). 'prod' is an alias of 'full'."),
    )
    validate.add_argument(
        "--run-id",
        dest="run_id",
        default=None,
        help="Optional run identifier.",
    )
    validate.add_argument(
        "--odoo-versions",
        dest="odoo_versions",
        default="17,18,19",
        help="Comma-separated Odoo major versions (default: 17,18,19).",
    )

    subparsers.add_parser("version", help="Show repository and protocol version metadata.")
    subparsers.add_parser(
        "capabilities",
        help="Show supported profiles, pipeline stages, and capabilities.",
    )
    subparsers.add_parser("help", help="Show CLI usage and examples.")

    return parser
