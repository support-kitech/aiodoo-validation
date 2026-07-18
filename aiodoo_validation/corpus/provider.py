"""Configurable evaluation corpus provider (E5) with pin verification (E7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aiodoo_validation.corpus.catalog import (
    CorpusPinRegistry,
    builtin_corpus_pin_registry,
    verify_loaded_against_registry,
)
from aiodoo_validation.corpus.exceptions import CorpusLoadError, CorpusPinError
from aiodoo_validation.corpus.gates import GatePurpose
from aiodoo_validation.corpus.loader import JsonlCorpusLoader, LoadedCorpus
from aiodoo_validation.corpus.pinning import (
    resolve_pin_location,
    verify_loaded_corpus_against_pin,
)

# Request / plan configuration key for evaluation corpora (filesystem location).
EVALUATION_CORPUS_PATH_KEY = "evaluation_corpus_path"


@dataclass(frozen=True, slots=True)
class ConfigurableCorpusProvider:
    """
    Load evaluation corpora from configured paths.

    - Missing / empty path → ``None`` (caller defers behavioral evaluation)
    - Invalid path / gate failure → raises (fail closed; never silent defer)
    - When a pin registry is present, known corpus identities are verified
      against the pin after load (E7). Unknown path-only corpora still load.
    """

    loader: JsonlCorpusLoader = JsonlCorpusLoader()
    pin_registry: CorpusPinRegistry | None = field(default_factory=builtin_corpus_pin_registry)

    def resolve_path(self, configured: object | None) -> Path | None:
        if configured is None:
            return None
        if not isinstance(configured, (str, Path)):
            raise CorpusLoadError(f"{EVALUATION_CORPUS_PATH_KEY} must be a string path when set.")
        text = str(configured).strip()
        if not text:
            return None
        return Path(text)

    def load(
        self,
        configured_path: object | None,
        *,
        purpose: GatePurpose = "production_behavior",
        capability_id: str | None = None,
        configured_corpus_id: str | None = None,
    ) -> LoadedCorpus | None:
        path = self.resolve_path(configured_path)
        if path is None:
            return None
        loaded = self.loader.load(path, purpose=purpose)
        if self.pin_registry is not None:
            verify_loaded_against_registry(
                loaded,
                registry=self.pin_registry,
                capability_id=capability_id,
                configured_corpus_id=configured_corpus_id,
            )
        return loaded

    def load_by_identity(
        self,
        corpus_ref: str,
        *,
        capability_id: str,
        explicit_path: object | None = None,
        purpose: GatePurpose = "production_behavior",
    ) -> LoadedCorpus:
        """Load a corpus by stable identity via the pin registry."""
        if self.pin_registry is None:
            raise CorpusPinError(
                "load_by_identity requires a pin_registry on ConfigurableCorpusProvider."
            )
        pin = self.pin_registry.require_for_capability(
            corpus_ref,
            capability_id=capability_id,
        )
        path_override = self.resolve_path(explicit_path)
        location = resolve_pin_location(
            pin,
            search_roots=self.pin_registry.search_roots,
            location_overrides=self.pin_registry.location_overrides(),
            explicit_path=path_override,
        )
        loaded = self.loader.load(
            location,
            purpose=purpose,
            additional_denied_fingerprints=pin.additional_denied_fingerprints,
        )
        verify_loaded_corpus_against_pin(loaded, pin)
        return loaded


__all__ = [
    "EVALUATION_CORPUS_PATH_KEY",
    "ConfigurableCorpusProvider",
]
