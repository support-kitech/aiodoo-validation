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
    "aiodoo_validation/ports",
    "aiodoo_validation/stubs",
    "aiodoo_validation/engine",
    "aiodoo_validation/resolution",
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
    "docs/implementation_status.md",
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
    assert "[project]" not in text
    assert "[tool.ruff]" in text
    assert "[tool.mypy]" in text
