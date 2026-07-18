"""Production corpus governance — identity → pin → location → load (E7).

Does not replace ``JsonlCorpusLoader``. Fingerprint / role gates remain in
``corpus.gates`` via the existing loader.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from aiodoo_validation.corpus.catalog import (
    EVALUATION_CORPUS_ID_KEY,
    CorpusPinRegistry,
    builtin_corpus_pin_registry,
)
from aiodoo_validation.corpus.gates import GatePurpose
from aiodoo_validation.corpus.loader import JsonlCorpusLoader, LoadedCorpus
from aiodoo_validation.corpus.pinning import (
    CorpusPin,
    resolve_pin_location,
    verify_loaded_corpus_against_pin,
)
from aiodoo_validation.corpus.provider import EVALUATION_CORPUS_PATH_KEY


@dataclass(frozen=True, slots=True)
class CorpusLookupResult:
    """Resolved production corpus selection."""

    pin: CorpusPin
    location: Path
    loaded: LoadedCorpus
    corpus_ref: str


@dataclass(frozen=True, slots=True)
class ProductionCorpusLookup:
    """
    Governed lookup: capability-scoped identity → pin → path → loaded corpus.

    Filesystem paths remain an implementation detail used only after identity
    resolution (or as an explicit location override for a pin).
    """

    registry: CorpusPinRegistry = field(default_factory=builtin_corpus_pin_registry)
    loader: JsonlCorpusLoader = JsonlCorpusLoader()

    def lookup(
        self,
        corpus_ref: str,
        *,
        capability_id: str,
        explicit_path: Path | str | None = None,
        purpose: GatePurpose = "production_behavior",
    ) -> CorpusLookupResult:
        pin = self.registry.require_for_capability(
            corpus_ref,
            capability_id=capability_id,
        )
        location = resolve_pin_location(
            pin,
            search_roots=self.registry.search_roots,
            location_overrides=self.registry.location_overrides(),
            explicit_path=explicit_path,
        )
        loaded = self.loader.load(
            location,
            purpose=purpose,
            additional_denied_fingerprints=pin.additional_denied_fingerprints,
        )
        verify_loaded_corpus_against_pin(loaded, pin)
        return CorpusLookupResult(
            pin=pin,
            location=location,
            loaded=loaded,
            corpus_ref=self.registry.resolve_id(corpus_ref),
        )

    def lookup_default_for_capability(
        self,
        capability_id: str,
        *,
        explicit_path: Path | str | None = None,
        purpose: GatePurpose = "production_behavior",
    ) -> CorpusLookupResult | None:
        """
        Load the catalog default pin for a capability when one is declared.

        Returns ``None`` when no default is registered. Callers that must honor
        G11 (defer without configuration) should not invoke this implicitly.
        """
        pin = self.registry.default_for_capability(capability_id)
        if pin is None:
            return None
        return self.lookup(
            pin.corpus_id,
            capability_id=capability_id,
            explicit_path=explicit_path,
            purpose=purpose,
        )


def resolve_evaluation_corpus_configuration(
    *,
    capability_id: str,
    metadata: Mapping[str, Any],
    registry: CorpusPinRegistry | None = None,
) -> Mapping[str, Any]:
    """
    Resolve request metadata into plan configuration for corpus selection.

    Rules:
    - No id and no path → empty (caller defers; G11)
    - ``evaluation_corpus_id`` → resolve location; path is implementation detail
    - path-only → forward path (legacy E5); pin verify happens later if known
    - id + path → id selects pin; path overrides location only
    """
    catalog = registry or builtin_corpus_pin_registry()
    raw_id = metadata.get(EVALUATION_CORPUS_ID_KEY)
    raw_path = metadata.get(EVALUATION_CORPUS_PATH_KEY)

    corpus_id = str(raw_id).strip() if raw_id is not None else ""
    corpus_path = str(raw_path).strip() if raw_path is not None else ""

    if not corpus_id and not corpus_path:
        return MappingProxyType({})

    if corpus_id:
        pin = catalog.require_for_capability(corpus_id, capability_id=capability_id)
        location = resolve_pin_location(
            pin,
            search_roots=catalog.search_roots,
            location_overrides=catalog.location_overrides(),
            explicit_path=corpus_path or None,
        )
        return MappingProxyType(
            {
                EVALUATION_CORPUS_ID_KEY: pin.corpus_id,
                EVALUATION_CORPUS_PATH_KEY: str(location),
            }
        )

    # Path-only legacy selection.
    return MappingProxyType({EVALUATION_CORPUS_PATH_KEY: corpus_path})


__all__ = [
    "CorpusLookupResult",
    "ProductionCorpusLookup",
    "resolve_evaluation_corpus_configuration",
]
