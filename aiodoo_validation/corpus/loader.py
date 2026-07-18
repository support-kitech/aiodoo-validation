"""JsonlCorpusLoader — load manifest + JSONL and apply fail-closed gates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiodoo_validation.corpus.exceptions import CorpusLoadError
from aiodoo_validation.corpus.gates import (
    CorpusGateResult,
    GatePurpose,
    evaluate_corpus_manifest,
    require_corpus_manifest,
)
from aiodoo_validation.corpus.jsonl import fingerprint_file, load_jsonl_records
from aiodoo_validation.corpus.manifest import load_corpus_manifest
from aiodoo_validation.domain.corpus import CorpusManifest

DEFAULT_MANIFEST_NAME = "manifest.json"
DEFAULT_RECORDS_NAME = "records.jsonl"


@dataclass(frozen=True, slots=True)
class LoadedCorpus:
    """Immutable result of loading a corpus directory."""

    manifest: CorpusManifest
    records: tuple[Mapping[str, Any], ...]
    corpus_dir: Path
    manifest_path: Path
    records_path: Path
    computed_fingerprint: str
    gate: CorpusGateResult


@dataclass(frozen=True, slots=True)
class JsonlCorpusLoader:
    """
    Generic corpus directory loader.

    Expected layout::

        <corpus_dir>/
          manifest.json
          records.jsonl

    Records are raw JSON objects — no capability schema interpretation.
    """

    manifest_filename: str = DEFAULT_MANIFEST_NAME
    records_filename: str = DEFAULT_RECORDS_NAME

    def load(
        self,
        corpus_dir: Path | str,
        *,
        purpose: GatePurpose = "production_behavior",
        max_records: int | None = None,
        additional_denied_fingerprints: Sequence[str] = (),
        enforce_gates: bool = True,
    ) -> LoadedCorpus:
        root = Path(corpus_dir)
        if not str(corpus_dir).strip():
            raise CorpusLoadError("Corpus path must be non-empty.")
        if not root.exists():
            raise CorpusLoadError(f"Corpus path does not exist: {root}")
        if not root.is_dir():
            raise CorpusLoadError(f"Corpus path is not a directory: {root}")

        manifest_path = root / self.manifest_filename
        records_path = root / self.records_filename
        if not manifest_path.is_file():
            raise CorpusLoadError(f"Corpus manifest missing: {manifest_path}")
        if not records_path.is_file():
            raise CorpusLoadError(f"Corpus JSONL missing: {records_path}")

        manifest = load_corpus_manifest(manifest_path)
        computed = fingerprint_file(records_path)
        records = load_jsonl_records(records_path, max_records=max_records)

        if enforce_gates:
            gate = require_corpus_manifest(
                manifest,
                purpose=purpose,
                computed_fingerprint=computed,
                additional_denied_fingerprints=additional_denied_fingerprints,
            )
        else:
            gate = evaluate_corpus_manifest(
                manifest,
                purpose=purpose,
                computed_fingerprint=computed,
                additional_denied_fingerprints=additional_denied_fingerprints,
            )

        return LoadedCorpus(
            manifest=manifest,
            records=records,
            corpus_dir=root.resolve(),
            manifest_path=manifest_path.resolve(),
            records_path=records_path.resolve(),
            computed_fingerprint=computed,
            gate=gate,
        )


__all__ = [
    "DEFAULT_MANIFEST_NAME",
    "DEFAULT_RECORDS_NAME",
    "JsonlCorpusLoader",
    "LoadedCorpus",
]
