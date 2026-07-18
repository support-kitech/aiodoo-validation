"""Corpus pin registry and builtin production catalog (E7)."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from aiodoo_validation.corpus.exceptions import CorpusPinError
from aiodoo_validation.corpus.loader import LoadedCorpus
from aiodoo_validation.corpus.pinning import CorpusPin, verify_loaded_corpus_against_pin

# Request / plan configuration key for stable corpus identity (not a path).
EVALUATION_CORPUS_ID_KEY = "evaluation_corpus_id"

# Optional override roots for resolving ``location_hint`` values.
EVAL_CORPUS_ROOT_ENV = "AIODOO_EVAL_CORPUS_ROOT"

# Repair evaluation fixture pin (validation-owned held-out smoke corpus).
# Identity matches tests/fixtures/capabilities/repair/eval_corpus/manifest.json.
REPAIR_EVAL_FIXTURE_CORPUS_ID = "fixture.repair.eval.behavior"
REPAIR_EVAL_FIXTURE_FINGERPRINT = "dc418ad42216d8296dce5bb862372c8c38b301a97d508586cbf22d388ecd400f"
REPAIR_EVAL_FIXTURE_VERSION = "fixture-e5"

# Coding evaluation fixture pin (validation-owned held-out smoke corpus).
CODING_EVAL_FIXTURE_CORPUS_ID = "fixture.coding.eval.behavior"
CODING_EVAL_FIXTURE_FINGERPRINT = "1e7a1464641382dea9045e1207d2d777560d0e1c0a6c9bb71707bb123fe01dc5"
CODING_EVAL_FIXTURE_VERSION = "fixture-coding-e5"

# Planner evaluation fixture pin (validation-owned held-out smoke corpus).
PLANNER_EVAL_FIXTURE_CORPUS_ID = "fixture.planner.eval.behavior"
PLANNER_EVAL_FIXTURE_FINGERPRINT = (
    "28804a8d7c25ce39eb5ac27605c157c1fccd3b7eac770d39c5cb57dd7bf3eaab"
)
PLANNER_EVAL_FIXTURE_VERSION = "fixture-planner-e5"


def _repair_eval_fixture_pin() -> CorpusPin:
    return CorpusPin(
        corpus_id=REPAIR_EVAL_FIXTURE_CORPUS_ID,
        capability_id="repair",
        fingerprint=REPAIR_EVAL_FIXTURE_FINGERPRINT,
        dataset_version=REPAIR_EVAL_FIXTURE_VERSION,
        source_package="aiodoo-validation-fixtures",
        location_hint="repair/eval_corpus",
        metadata=MappingProxyType({"kind": "validation_fixture_pin"}),
    )


def _coding_eval_fixture_pin() -> CorpusPin:
    return CorpusPin(
        corpus_id=CODING_EVAL_FIXTURE_CORPUS_ID,
        capability_id="coding",
        fingerprint=CODING_EVAL_FIXTURE_FINGERPRINT,
        dataset_version=CODING_EVAL_FIXTURE_VERSION,
        source_package="aiodoo-validation-fixtures",
        location_hint="coding/eval_corpus",
        metadata=MappingProxyType({"kind": "validation_fixture_pin"}),
    )


def _planner_eval_fixture_pin() -> CorpusPin:
    return CorpusPin(
        corpus_id=PLANNER_EVAL_FIXTURE_CORPUS_ID,
        capability_id="planner",
        fingerprint=PLANNER_EVAL_FIXTURE_FINGERPRINT,
        dataset_version=PLANNER_EVAL_FIXTURE_VERSION,
        source_package="aiodoo-validation-fixtures",
        location_hint="planner/eval_corpus",
        metadata=MappingProxyType({"kind": "validation_fixture_pin"}),
    )


def _fixture_package_root() -> Path:
    """tests/fixtures/capabilities — used as a default search root for pins."""
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "capabilities"


@dataclass(frozen=True, slots=True)
class CorpusPinRegistry:
    """
    Registry of production corpus pins.

    Capabilities declare requirements; this registry declares which corpus
    identities are approved for production selection.
    """

    _pins: Mapping[str, CorpusPin] = field(default_factory=lambda: MappingProxyType({}))
    _aliases: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    _locations: Mapping[str, Path] = field(default_factory=lambda: MappingProxyType({}))
    _capability_defaults: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    search_roots: tuple[Path, ...] = ()

    @classmethod
    def empty(cls) -> CorpusPinRegistry:
        return cls()

    @classmethod
    def build(
        cls,
        pins: Sequence[CorpusPin],
        *,
        aliases: Mapping[str, str] | None = None,
        locations: Mapping[str, Path | str] | None = None,
        capability_defaults: Mapping[str, str] | None = None,
        search_roots: Sequence[Path | str] = (),
    ) -> CorpusPinRegistry:
        pin_map: dict[str, CorpusPin] = {}
        for pin in pins:
            if pin.corpus_id in pin_map:
                raise CorpusPinError(f"Duplicate corpus pin id {pin.corpus_id!r}.")
            pin_map[pin.corpus_id] = pin

        alias_map: dict[str, str] = {}
        for alias, target in dict(aliases or {}).items():
            key = str(alias).strip()
            value = str(target).strip()
            if not key or not value:
                raise CorpusPinError("Alias keys and targets must be non-empty.")
            if value not in pin_map:
                raise CorpusPinError(f"Alias {key!r} targets unknown corpus_id {value!r}.")
            alias_map[key] = value

        location_map: dict[str, Path] = {}
        for corpus_id, raw in dict(locations or {}).items():
            if corpus_id not in pin_map:
                raise CorpusPinError(f"Location registered for unknown corpus_id {corpus_id!r}.")
            location_map[corpus_id] = Path(raw)

        defaults: dict[str, str] = {}
        for capability_id, corpus_id in dict(capability_defaults or {}).items():
            cap = str(capability_id).strip()
            cid = str(corpus_id).strip()
            if not cap or not cid:
                raise CorpusPinError("capability_defaults entries must be non-empty.")
            if cid not in pin_map:
                raise CorpusPinError(
                    f"capability default for {cap!r} references unknown corpus_id {cid!r}."
                )
            if pin_map[cid].capability_id != cap:
                raise CorpusPinError(
                    f"capability default for {cap!r} points to pin "
                    f"{cid!r} owned by {pin_map[cid].capability_id!r}."
                )
            defaults[cap] = cid

        roots = tuple(Path(root) for root in search_roots if str(root).strip())
        return cls(
            _pins=MappingProxyType(pin_map),
            _aliases=MappingProxyType(alias_map),
            _locations=MappingProxyType(location_map),
            _capability_defaults=MappingProxyType(defaults),
            search_roots=roots,
        )

    def resolve_id(self, corpus_ref: str) -> str:
        ref = corpus_ref.strip()
        if not ref:
            raise CorpusPinError("corpus identity must be non-empty.")
        if ref in self._pins:
            return ref
        if ref in self._aliases:
            return self._aliases[ref]
        raise CorpusPinError(f"Unknown corpus identity {corpus_ref!r}.")

    def get(self, corpus_ref: str) -> CorpusPin:
        return self._pins[self.resolve_id(corpus_ref)]

    def get_optional(self, corpus_ref: str) -> CorpusPin | None:
        try:
            return self.get(corpus_ref)
        except CorpusPinError:
            return None

    def require_for_capability(self, corpus_ref: str, *, capability_id: str) -> CorpusPin:
        pin = self.get(corpus_ref)
        if pin.capability_id != capability_id:
            raise CorpusPinError(
                f"Corpus {pin.corpus_id!r} belongs to capability "
                f"{pin.capability_id!r}, not {capability_id!r}."
            )
        return pin

    def default_for_capability(self, capability_id: str) -> CorpusPin | None:
        corpus_id = self._capability_defaults.get(capability_id)
        if corpus_id is None:
            return None
        return self._pins[corpus_id]

    def location_overrides(self) -> Mapping[str, Path]:
        return self._locations

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._pins))

    def aliases(self) -> Mapping[str, str]:
        return self._aliases


def search_roots_from_environment(
    *,
    extra_roots: Sequence[Path | str] = (),
) -> tuple[Path, ...]:
    """Build search roots from env + optional extras (first wins on ambiguity)."""
    roots: list[Path] = []
    env_root = os.environ.get(EVAL_CORPUS_ROOT_ENV, "").strip()
    if env_root:
        roots.append(Path(env_root))
    roots.extend(Path(root) for root in extra_roots if str(root).strip())
    # Deduplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        resolved = root.resolve() if root.exists() else root
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(root)
    return tuple(unique)


def builtin_corpus_pin_registry(
    *,
    include_fixture_locations: bool = True,
    extra_search_roots: Sequence[Path | str] = (),
) -> CorpusPinRegistry:
    """
    Builtin production pin catalog.

    Ships Repair, Coding, and Planner evaluation fixture pins. Does **not**
    auto-select them for production runs (G11: missing config still defers).
    Callers must pass ``evaluation_corpus_id`` (or a path) explicitly.
    """
    repair_pin = _repair_eval_fixture_pin()
    coding_pin = _coding_eval_fixture_pin()
    planner_pin = _planner_eval_fixture_pin()
    fixture_root = _fixture_package_root()
    locations: dict[str, Path] = {}
    if include_fixture_locations and fixture_root.is_dir():
        locations[repair_pin.corpus_id] = fixture_root / "repair" / "eval_corpus"
        locations[coding_pin.corpus_id] = fixture_root / "coding" / "eval_corpus"
        locations[planner_pin.corpus_id] = fixture_root / "planner" / "eval_corpus"

    return CorpusPinRegistry.build(
        (repair_pin, coding_pin, planner_pin),
        aliases={
            "repair.eval": repair_pin.corpus_id,
            "repair.eval.fixture": repair_pin.corpus_id,
            "coding.eval": coding_pin.corpus_id,
            "coding.eval.fixture": coding_pin.corpus_id,
            "planner.eval": planner_pin.corpus_id,
            "planner.eval.fixture": planner_pin.corpus_id,
        },
        locations=locations,
        # Documented default identities — not auto-loaded without configuration.
        capability_defaults={
            "repair": repair_pin.corpus_id,
            "coding": coding_pin.corpus_id,
            "planner": planner_pin.corpus_id,
        },
        search_roots=search_roots_from_environment(extra_roots=(fixture_root, *extra_search_roots)),
    )


def verify_loaded_against_registry(
    loaded: LoadedCorpus,
    *,
    registry: CorpusPinRegistry,
    capability_id: str | None = None,
    configured_corpus_id: str | None = None,
) -> CorpusPin | None:
    """
    If the loaded corpus (or configured id) is pinned, verify it.

    Unknown corpora (path-only fixtures not in the catalog) are allowed without
    pin verification so E5 path workflows remain valid.
    """
    pin: CorpusPin | None
    if configured_corpus_id:
        pin = registry.get(configured_corpus_id)
        if capability_id is not None and pin.capability_id != capability_id:
            raise CorpusPinError(
                f"Configured corpus {pin.corpus_id!r} belongs to "
                f"{pin.capability_id!r}, not {capability_id!r}."
            )
    else:
        pin = registry.get_optional(loaded.manifest.corpus_id)

    if pin is None:
        return None

    if capability_id is not None and pin.capability_id != capability_id:
        raise CorpusPinError(
            f"Loaded corpus {loaded.manifest.corpus_id!r} pin belongs to "
            f"{pin.capability_id!r}, not {capability_id!r}."
        )
    verify_loaded_corpus_against_pin(loaded, pin)
    return pin


__all__ = [
    "EVALUATION_CORPUS_ID_KEY",
    "EVAL_CORPUS_ROOT_ENV",
    "CODING_EVAL_FIXTURE_CORPUS_ID",
    "CODING_EVAL_FIXTURE_FINGERPRINT",
    "CODING_EVAL_FIXTURE_VERSION",
    "PLANNER_EVAL_FIXTURE_CORPUS_ID",
    "PLANNER_EVAL_FIXTURE_FINGERPRINT",
    "PLANNER_EVAL_FIXTURE_VERSION",
    "REPAIR_EVAL_FIXTURE_CORPUS_ID",
    "REPAIR_EVAL_FIXTURE_FINGERPRINT",
    "REPAIR_EVAL_FIXTURE_VERSION",
    "CorpusPinRegistry",
    "builtin_corpus_pin_registry",
    "search_roots_from_environment",
    "verify_loaded_against_registry",
]
