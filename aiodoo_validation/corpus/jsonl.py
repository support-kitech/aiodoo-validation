"""Generic JSONL record loading (raw dicts only)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aiodoo_validation.corpus.exceptions import CorpusLoadError


def fingerprint_file(path: Path | str) -> str:
    """Return SHA-256 hex digest of file bytes."""
    file_path = Path(path)
    digest = hashlib.sha256()
    try:
        with file_path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise CorpusLoadError(f"Failed to fingerprint corpus file: {file_path}") from exc
    return digest.hexdigest()


def load_jsonl_records(
    path: Path | str,
    *,
    max_records: int | None = None,
) -> tuple[Mapping[str, Any], ...]:
    """
    Load JSONL as an ordered tuple of JSON objects.

    Does not interpret capability schemas. Each non-empty line must be a JSON object.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise CorpusLoadError(f"Corpus JSONL not found: {file_path}")
    if max_records is not None and max_records < 0:
        raise CorpusLoadError("max_records must be >= 0 when provided.")

    records: list[Mapping[str, Any]] = []
    try:
        with file_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                if max_records is not None and len(records) >= max_records:
                    break
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise CorpusLoadError(
                        f"Malformed JSONL at {file_path}:{line_number}: {exc.msg}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise CorpusLoadError(
                        f"JSONL line {line_number} in {file_path} must be a JSON object."
                    )
                records.append(payload)
    except OSError as exc:
        raise CorpusLoadError(f"Failed to read corpus JSONL: {file_path}") from exc

    return tuple(records)


__all__ = [
    "fingerprint_file",
    "load_jsonl_records",
]
