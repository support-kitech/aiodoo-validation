"""CLI application entry point (Phase 10)."""

from __future__ import annotations

import argparse
import sys

from aiodoo_validation.cli.commands import dispatch
from aiodoo_validation.cli.config import CliConfig
from aiodoo_validation.cli.exit_codes import EXIT_FAILED, EXIT_INVALID_REQUEST
from aiodoo_validation.cli.formatter import ConsoleFormatter
from aiodoo_validation.cli.parser import build_parser
from aiodoo_validation.exceptions import InvalidRequestError


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, execute the selected command, and return a process exit code."""
    config = CliConfig.from_env()
    parser = build_parser(config)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return EXIT_INVALID_REQUEST
        if isinstance(code, int):
            return code
        return EXIT_INVALID_REQUEST

    if args.debug:
        config = CliConfig(program_name=config.program_name, debug=True)

    if args.command is None:
        return dispatch(argparse.Namespace(command="help"), config=config)

    try:
        return dispatch(args, config=config)
    except InvalidRequestError as exc:
        sys.stdout.write(ConsoleFormatter().format_error(str(exc)))
        return EXIT_INVALID_REQUEST
    except Exception as exc:  # noqa: BLE001 — CLI must not crash on unexpected errors
        if config.debug:
            raise
        sys.stdout.write(
            ConsoleFormatter().format_error(f"Unexpected CLI error: {exc}")
        )
        return EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
