"""Unit tests for Phase 10 Production CLI."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from aiodoo_validation.cli.app import main
from aiodoo_validation.cli.config import CliConfig
from aiodoo_validation.cli.exit_codes import (
    EXIT_CERTIFIED,
    EXIT_FAILED,
    EXIT_INVALID_REQUEST,
    EXIT_NOT_CERTIFIED,
    exit_code_for_status,
)
from aiodoo_validation.cli.formatter import ConsoleFormatter
from aiodoo_validation.cli.parser import build_parser
from aiodoo_validation.domain.enums import ExitStatus, ValidationStage
from aiodoo_validation.domain.request import ValidationRequest
from aiodoo_validation.domain.result import ValidationRunResult
from aiodoo_validation.engine import ValidationEngine

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "aiodoo_validation"
CLI_DIR = PACKAGE / "cli"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "artifacts"


def test_parser_validate_requires_artifact_arguments() -> None:
    parser = build_parser(CliConfig())
    with pytest.raises(SystemExit):
        parser.parse_args(["validate", "--base-model", "./base"])


def test_parser_validate_accepts_required_arguments() -> None:
    parser = build_parser(CliConfig())
    args = parser.parse_args(
        [
            "validate",
            "--profile",
            "coding",
            "--base-model",
            "./base",
            "--adapter",
            "./adapter",
        ]
    )
    assert args.command == "validate"
    assert args.profile == "coding"
    assert args.base_model == "./base"
    assert args.adapter == "./adapter"


def test_parser_version_and_capabilities_commands() -> None:
    parser = build_parser(CliConfig())
    assert parser.parse_args(["version"]).command == "version"
    assert parser.parse_args(["capabilities"]).command == "capabilities"
    assert parser.parse_args(["help"]).command == "help"


def test_exit_code_mapping() -> None:
    assert exit_code_for_status(ExitStatus.COMPLETED) == EXIT_CERTIFIED
    assert exit_code_for_status(ExitStatus.NOT_CERTIFIED) == EXIT_NOT_CERTIFIED
    assert exit_code_for_status(ExitStatus.FAILED) == EXIT_FAILED
    assert exit_code_for_status(ExitStatus.INVALID_REQUEST) == EXIT_INVALID_REQUEST
    assert exit_code_for_status(ExitStatus.INTERNAL_ERROR) == EXIT_FAILED


def test_version_command_prints_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["version"])
    output = capsys.readouterr().out
    assert code == 0
    assert "Repository version:" in output
    assert "Protocol version:" in output
    assert "coding" in output
    assert "standard" in output


def test_capabilities_command_prints_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["capabilities"])
    output = capsys.readouterr().out
    assert code == 0
    assert "Supported profiles:" in output
    assert "Pipeline stages:" in output
    assert ValidationStage.REPORT.value in output
    assert "supports_reports" in output


def test_help_command_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["help"])
    output = capsys.readouterr().out
    assert code == 0
    assert "validate" in output
    assert "version" in output
    assert "capabilities" in output


def test_default_invocation_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    code = main([])
    output = capsys.readouterr().out
    assert code == 0
    assert "Usage:" in output


def test_validate_invalid_profile_returns_exit_code_3(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "validate",
            "--profile",
            "planner",
            "--base-model",
            "base",
            "--adapter",
            "adapter",
        ]
    )
    output = capsys.readouterr().out
    assert code == EXIT_INVALID_REQUEST
    assert "Unsupported profile_name" in output


def test_validate_invalid_odoo_versions_returns_exit_code_3(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "validate",
            "--base-model",
            "base",
            "--adapter",
            "adapter",
            "--odoo-versions",
            "99",
        ]
    )
    output = capsys.readouterr().out
    assert code == EXIT_INVALID_REQUEST
    assert "Unsupported Odoo version" in output


def test_validate_runs_engine_and_formats_output(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "validate",
            "--profile",
            "coding",
            "--base-model",
            str(FIXTURES / "base_model"),
            "--adapter",
            str(FIXTURES / "coding_adapter"),
            "--execution-tier",
            "standard",
        ]
    )
    output = capsys.readouterr().out
    assert code == EXIT_NOT_CERTIFIED
    assert "Exit status: not_certified" in output
    assert "Pipeline stages:" in output
    assert "Report summary:" in output
    assert "coding.report.metadata" in output


def test_validate_pipeline_failure_returns_exit_code_2(capsys: pytest.CaptureFixture[str]) -> None:
    request = ValidationRequest(
        profile_name="coding",
        base_model_ref="/nonexistent/base",
        adapter_ref="/nonexistent/adapter",
    )
    failed = ValidationRunResult(
        exit_status=ExitStatus.FAILED,
        run_context=ValidationEngine.with_stubs().run(request).run_context,
        message="Validation lifecycle failed.",
        completed_at=ValidationEngine.with_stubs().run(request).completed_at,
    )
    with patch("aiodoo_validation.cli.commands.ValidationEngine.with_filesystem") as factory:
        factory.return_value.run.return_value = failed
        code = main(
            [
                "validate",
                "--base-model",
                "/nonexistent/base",
                "--adapter",
                "/nonexistent/adapter",
            ]
        )
    output = capsys.readouterr().out
    assert code == EXIT_FAILED
    assert "Exit status: failed" in output


def test_validate_unexpected_error_without_debug(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("aiodoo_validation.cli.commands.ValidationEngine.with_filesystem") as factory:
        factory.return_value.run.side_effect = RuntimeError("boom")
        code = main(
            [
                "validate",
                "--base-model",
                str(FIXTURES / "base_model"),
                "--adapter",
                str(FIXTURES / "coding_adapter"),
            ]
        )
    output = capsys.readouterr().out
    assert code == EXIT_FAILED
    assert "Unexpected" in output or "failed unexpectedly" in output


def test_formatter_includes_warnings_and_errors() -> None:
    request = ValidationRequest(
        profile_name="coding",
        base_model_ref="base",
        adapter_ref="adapter",
    )
    engine_result = ValidationEngine.with_stubs().run(request)
    context = engine_result.run_context.with_warning("warn-1").with_error("err-1")
    result = ValidationRunResult(
        exit_status=engine_result.exit_status,
        run_context=context,
        message=engine_result.message,
        completed_at=engine_result.completed_at,
    )
    output = ConsoleFormatter().format(result)
    assert "warn-1" in output
    assert "err-1" in output
    assert "Report summary:" in output


def test_console_script_entry_point_invokes_main() -> None:
    script = ROOT / "scripts" / "aiodoo-validation"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "aiodoo_validation.cli.app import main" in text


def test_cli_does_not_import_upstream_execution_modules() -> None:
    forbidden_suffixes = (
        "oracles.engine",
        "oracles.registry",
        "oracles.placeholders",
        "oracles.base",
        "scoring.engine",
        "scoring.registry",
        "scoring.policies",
        "scoring.base",
        "benchmark.engine",
        "benchmark.registry",
        "benchmark.policies",
        "benchmark.base",
        "certification.engine",
        "certification.registry",
        "certification.policies",
        "certification.base",
        "reporting.engine",
        "reporting.registry",
        "reporting.templates",
        "reporting.base",
    )
    violations: list[str] = []
    for path in CLI_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
                if module.endswith(forbidden_suffixes) or module in {
                    "aiodoo_validation.oracles",
                    "aiodoo_validation.scoring",
                    "aiodoo_validation.benchmark",
                    "aiodoo_validation.certification",
                    "aiodoo_validation.reporting",
                }:
                    violations.append(f"{path.relative_to(ROOT)}: {module}")
    assert not violations, "cli must not import upstream execution modules:\n" + "\n".join(
        violations
    )


def test_main_module_entrypoint_source() -> None:
    main_module = ROOT / "aiodoo_validation" / "__main__.py"
    text = main_module.read_text(encoding="utf-8")
    assert "from aiodoo_validation.cli.app import main" in text
    assert "sys.exit(main())" in text
