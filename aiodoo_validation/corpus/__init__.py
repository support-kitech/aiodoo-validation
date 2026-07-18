"""Generic evaluation corpus infrastructure (Capability Delivery E1)."""

from aiodoo_validation.corpus.exceptions import (
    CorpusError,
    CorpusGateError,
    CorpusLoadError,
)
from aiodoo_validation.corpus.gates import (
    CorpusGateResult,
    evaluate_corpus_manifest,
    require_corpus_manifest,
)
from aiodoo_validation.corpus.jsonl import fingerprint_file, load_jsonl_records
from aiodoo_validation.corpus.loader import (
    DEFAULT_MANIFEST_NAME,
    DEFAULT_RECORDS_NAME,
    JsonlCorpusLoader,
    LoadedCorpus,
)
from aiodoo_validation.corpus.manifest import (
    corpus_manifest_from_mapping,
    load_corpus_manifest,
)

__all__ = [
    "DEFAULT_MANIFEST_NAME",
    "DEFAULT_RECORDS_NAME",
    "CorpusError",
    "CorpusGateError",
    "CorpusGateResult",
    "CorpusLoadError",
    "JsonlCorpusLoader",
    "LoadedCorpus",
    "corpus_manifest_from_mapping",
    "evaluate_corpus_manifest",
    "fingerprint_file",
    "load_corpus_manifest",
    "load_jsonl_records",
    "require_corpus_manifest",
]
