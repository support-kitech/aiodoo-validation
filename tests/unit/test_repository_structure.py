"""Tests that required repository structure exists."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DIRS = [
    "docs/adr",
    "requirements",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    ".github/workflows",
    "aiodoo_validation/domain",
    "aiodoo_validation/corpus",
    "aiodoo_validation/transforms",
    "aiodoo_validation/capabilities",
    "aiodoo_validation/capabilities/repair",
    "aiodoo_validation/ports",
    "aiodoo_validation/stubs",
    "aiodoo_validation/engine",
    "aiodoo_validation/resolution",
    "aiodoo_validation/inference",
    "aiodoo_validation/profiles",
    "aiodoo_validation/profiles/base",
    "aiodoo_validation/profiles/coding",
    "aiodoo_validation/validation_plan",
    "aiodoo_validation/oracles",
    "aiodoo_validation/scoring",
    "aiodoo_validation/behavior",
    "aiodoo_validation/comparators",
    "aiodoo_validation/reports",
    "aiodoo_validation/reporting",
    "aiodoo_validation/cli",
    "aiodoo_validation/api",
    "aiodoo_validation/benchmark",
    "aiodoo_validation/certification",
]

REQUIRED_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "requirements/base.txt",
    "requirements/dev.txt",
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "docs/architecture.md",
    "docs/behavioral_validation.md",
    "docs/extensibility_refinements.md",
    "docs/implementation_status.md",
    "docs/SPECIFICATION_V1.md",
    "docs/capability_validation_contract.md",
    "docs/capability_specification.md",
    "docs/engineering_execution_plan.md",
    "docs/delivery_governance.md",
    "aiodoo_validation/capabilities/repair/capability.yaml",
    "docs/adr/0000-adr-template.md",
    ".github/workflows/ci.yml",
    ".editorconfig",
]

FORBIDDEN_FILES = [
    "setup.py",
    "setup.cfg",
]


@pytest.mark.parametrize("relative", REQUIRED_DIRS)
def test_required_directory_exists(relative: str) -> None:
    assert (ROOT / relative).is_dir(), f"Missing directory: {relative}"


@pytest.mark.parametrize("relative", REQUIRED_FILES)
def test_required_file_exists(relative: str) -> None:
    assert (ROOT / relative).is_file(), f"Missing file: {relative}"


@pytest.mark.parametrize("relative", FORBIDDEN_FILES)
def test_packaging_files_absent(relative: str) -> None:
    assert not (ROOT / relative).exists(), f"Must not exist: {relative}"


def test_no_egg_info_directory() -> None:
    assert not (ROOT / "aiodoo_validation.egg-info").exists()


def test_pyproject_is_tooling_only() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[build-system]" not in text
    assert "[project.scripts]" in text
    assert 'aiodoo-validation = "aiodoo_validation.cli.app:main"' in text
    assert "[tool.ruff]" in text
    assert "[tool.mypy]" in text
