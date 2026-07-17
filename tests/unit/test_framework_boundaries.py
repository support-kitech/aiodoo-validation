"""Framework boundary tests — ML and infrastructure isolation."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "aiodoo_validation"

FORBIDDEN_IMPORT_ROOTS = frozenset({"torch", "transformers", "peft", "datasets"})
ALLOWED_ML_FILES = frozenset(
    {
        PACKAGE / "inference" / "runtime" / "qwen.py",
    }
)


def _iter_python_files() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def _imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def test_ml_frameworks_confined_to_qwen_runtime() -> None:
    violations: list[str] = []
    for path in _iter_python_files():
        if path in ALLOWED_ML_FILES:
            continue
        imports = _imports_in_file(path)
        blocked = imports & FORBIDDEN_IMPORT_ROOTS
        if blocked:
            rel = path.relative_to(ROOT)
            violations.append(f"{rel}: {sorted(blocked)}")
    assert not violations, "ML frameworks must stay inside qwen runtime:\n" + "\n".join(violations)


def test_resolution_does_not_import_inference_package() -> None:
    resolution_dir = PACKAGE / "resolution"
    violations: list[str] = []
    for path in resolution_dir.rglob("*.py"):
        imports = _imports_in_file(path)
        if "inference" in imports:
            violations.append(str(path.relative_to(ROOT)))
    assert not violations, "resolution must not import inference:\n" + "\n".join(violations)
