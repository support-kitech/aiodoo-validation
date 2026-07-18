"""Generic evaluation corpus infrastructure (Capability Delivery E1 / E7)."""

from aiodoo_validation.corpus.catalog import (
    CODING_EVAL_FIXTURE_CORPUS_ID,
    CODING_EVAL_FIXTURE_FINGERPRINT,
    CODING_EVAL_FIXTURE_VERSION,
    CONVERSATION_EVAL_FIXTURE_CORPUS_ID,
    CONVERSATION_EVAL_FIXTURE_FINGERPRINT,
    CONVERSATION_EVAL_FIXTURE_VERSION,
    EVAL_CORPUS_ROOT_ENV,
    EVALUATION_CORPUS_ID_KEY,
    EXECUTION_EVAL_FIXTURE_CORPUS_ID,
    EXECUTION_EVAL_FIXTURE_FINGERPRINT,
    EXECUTION_EVAL_FIXTURE_VERSION,
    PLANNER_EVAL_FIXTURE_CORPUS_ID,
    PLANNER_EVAL_FIXTURE_FINGERPRINT,
    PLANNER_EVAL_FIXTURE_VERSION,
    REPAIR_EVAL_FIXTURE_CORPUS_ID,
    CorpusPinRegistry,
    builtin_corpus_pin_registry,
    search_roots_from_environment,
    verify_loaded_against_registry,
)
from aiodoo_validation.corpus.exceptions import (
    CorpusError,
    CorpusGateError,
    CorpusLoadError,
    CorpusPinError,
)
from aiodoo_validation.corpus.gates import (
    CorpusGateResult,
    evaluate_corpus_manifest,
    require_corpus_manifest,
)
from aiodoo_validation.corpus.governance import (
    CorpusLookupResult,
    ProductionCorpusLookup,
    resolve_evaluation_corpus_configuration,
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
from aiodoo_validation.corpus.pinning import (
    CorpusPin,
    resolve_pin_location,
    verify_loaded_corpus_against_pin,
)
from aiodoo_validation.corpus.provider import (
    EVALUATION_CORPUS_PATH_KEY,
    ConfigurableCorpusProvider,
)

__all__ = [
    "CODING_EVAL_FIXTURE_CORPUS_ID",
    "CODING_EVAL_FIXTURE_FINGERPRINT",
    "CODING_EVAL_FIXTURE_VERSION",
    "CONVERSATION_EVAL_FIXTURE_CORPUS_ID",
    "CONVERSATION_EVAL_FIXTURE_FINGERPRINT",
    "CONVERSATION_EVAL_FIXTURE_VERSION",
    "DEFAULT_MANIFEST_NAME",
    "DEFAULT_RECORDS_NAME",
    "EVALUATION_CORPUS_ID_KEY",
    "EVALUATION_CORPUS_PATH_KEY",
    "EVAL_CORPUS_ROOT_ENV",
    "EXECUTION_EVAL_FIXTURE_CORPUS_ID",
    "EXECUTION_EVAL_FIXTURE_FINGERPRINT",
    "EXECUTION_EVAL_FIXTURE_VERSION",
    "PLANNER_EVAL_FIXTURE_CORPUS_ID",
    "PLANNER_EVAL_FIXTURE_FINGERPRINT",
    "PLANNER_EVAL_FIXTURE_VERSION",
    "REPAIR_EVAL_FIXTURE_CORPUS_ID",
    "ConfigurableCorpusProvider",
    "CorpusError",
    "CorpusGateError",
    "CorpusGateResult",
    "CorpusLoadError",
    "CorpusLookupResult",
    "CorpusPin",
    "CorpusPinError",
    "CorpusPinRegistry",
    "JsonlCorpusLoader",
    "LoadedCorpus",
    "ProductionCorpusLookup",
    "builtin_corpus_pin_registry",
    "corpus_manifest_from_mapping",
    "evaluate_corpus_manifest",
    "fingerprint_file",
    "load_corpus_manifest",
    "load_jsonl_records",
    "require_corpus_manifest",
    "resolve_evaluation_corpus_configuration",
    "resolve_pin_location",
    "search_roots_from_environment",
    "verify_loaded_against_registry",
    "verify_loaded_corpus_against_pin",
]
