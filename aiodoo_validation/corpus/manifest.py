"""Parse CorpusManifest from JSON mappings (no capability schema knowledge)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aiodoo_validation.corpus.exceptions import CorpusLoadError
from aiodoo_validation.domain.corpus import CorpusManifest
from aiodoo_validation.domain.enums import CorpusRole
from aiodoo_validation.exceptions import DomainError


def _require_str(data: Mapping[str, Any], key: str) -> str:
    if key not in data:
        raise CorpusLoadError(f"Manifest missing required field {key!r}.")
    value = data[key]
    if not isinstance(value, str):
        raise CorpusLoadError(f"Manifest field {key!r} must be a string.")
    return value


def corpus_manifest_from_mapping(data: Mapping[str, Any]) -> CorpusManifest:
    """Build ``CorpusManifest`` from a plain mapping (JSON object)."""
    if not isinstance(data, Mapping):
        raise CorpusLoadError("Manifest root must be a JSON object.")

    role_raw = data.get("role")
    if not isinstance(role_raw, str) or not role_raw.strip():
        raise CorpusLoadError("Manifest field 'role' must be a non-empty string.")
    try:
        role = CorpusRole(role_raw.strip())
    except ValueError as exc:
        raise CorpusLoadError(
            f"Manifest field 'role' has unsupported value {role_raw!r}."
        ) from exc

    denied_raw = data.get("denied_training_fingerprints", ())
    if denied_raw is None:
        denied: tuple[str, ...] = ()
    elif isinstance(denied_raw, (list, tuple)):
        if not all(isinstance(item, str) for item in denied_raw):
            raise CorpusLoadError(
                "Manifest field 'denied_training_fingerprints' must be a list of strings."
            )
        denied = tuple(denied_raw)
    else:
        raise CorpusLoadError(
            "Manifest field 'denied_training_fingerprints' must be a list of strings."
        )

    source_package = data.get("source_package")
    if source_package is not None and not isinstance(source_package, str):
        raise CorpusLoadError("Manifest field 'source_package' must be a string when set.")

    metadata = data.get("metadata", {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        raise CorpusLoadError("Manifest field 'metadata' must be an object when set.")

    try:
        return CorpusManifest(
            corpus_id=_require_str(data, "corpus_id"),
            capability_id=_require_str(data, "capability_id"),
            role=role,
            dataset_version=_require_str(data, "dataset_version"),
            fingerprint=_require_str(data, "fingerprint"),
            source_package=source_package,
            denied_training_fingerprints=denied,
            metadata=dict(metadata),
        )
    except DomainError as exc:
        raise CorpusLoadError(str(exc)) from exc


def load_corpus_manifest(path: Path | str) -> CorpusManifest:
    """Load ``manifest.json`` from disk."""
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise CorpusLoadError(f"Corpus manifest not found: {manifest_path}")
    try:
        raw = manifest_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError as exc:
        raise CorpusLoadError(f"Failed to read corpus manifest: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise CorpusLoadError(
            f"Corpus manifest is not valid JSON: {manifest_path}"
        ) from exc
    if not isinstance(data, dict):
        raise CorpusLoadError("Corpus manifest root must be a JSON object.")
    return corpus_manifest_from_mapping(data)


__all__ = [
    "corpus_manifest_from_mapping",
    "load_corpus_manifest",
]
