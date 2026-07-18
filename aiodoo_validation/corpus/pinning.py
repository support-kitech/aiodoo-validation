"""Evaluation corpus pins — stable identity, not filesystem paths (E7).

Identity is ``corpus_id`` scoped by ``capability_id``, verified by
``fingerprint`` (+ optional ``dataset_version`` / ``source_package``).

Filesystem location is an implementation detail resolved via search roots,
location overrides, or explicit path configuration.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from aiodoo_validation.corpus.exceptions import CorpusLoadError, CorpusPinError
from aiodoo_validation.corpus.loader import LoadedCorpus


@dataclass(frozen=True, slots=True)
class CorpusPin:
    """
    Stable production identity for one evaluation corpus.

    Paths are never part of identity. ``location_hint`` is only a relative
    name under configured search roots.
    """

    corpus_id: str
    capability_id: str
    fingerprint: str
    dataset_version: str
    source_package: str | None = None
    location_hint: str | None = None
    additional_denied_fingerprints: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.corpus_id.strip():
            raise CorpusPinError("corpus_id must be non-empty.")
        if not self.capability_id.strip():
            raise CorpusPinError("capability_id must be non-empty.")
        if not self.fingerprint.strip():
            raise CorpusPinError("fingerprint must be non-empty.")
        if not self.dataset_version.strip():
            raise CorpusPinError("dataset_version must be non-empty.")
        if self.source_package is not None and not self.source_package.strip():
            raise CorpusPinError("source_package must be non-empty when provided.")
        if self.location_hint is not None and not self.location_hint.strip():
            raise CorpusPinError("location_hint must be non-empty when provided.")
        denied = tuple(str(item) for item in self.additional_denied_fingerprints)
        if len(denied) != len(set(denied)):
            raise CorpusPinError("additional_denied_fingerprints must be unique.")
        object.__setattr__(self, "additional_denied_fingerprints", denied)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType({str(k): str(v) for k, v in dict(self.metadata).items()}),
        )


def verify_loaded_corpus_against_pin(
    loaded: LoadedCorpus,
    pin: CorpusPin,
    *,
    require_capability_match: bool = True,
) -> None:
    """
    Verify a loaded corpus matches a pin.

    Reuses gate-verified fingerprint integrity on ``LoadedCorpus``; this check
    binds that corpus to the declared production identity (no re-hashing).
    """
    reasons: list[str] = []
    manifest = loaded.manifest

    if manifest.corpus_id != pin.corpus_id:
        reasons.append(
            f"corpus_id_mismatch:manifest={manifest.corpus_id!r},pin={pin.corpus_id!r}"
        )
    if require_capability_match and manifest.capability_id != pin.capability_id:
        reasons.append(
            "capability_id_mismatch:"
            f"manifest={manifest.capability_id!r},pin={pin.capability_id!r}"
        )
    if manifest.fingerprint != pin.fingerprint:
        reasons.append("fingerprint_mismatch_against_pin")
    if loaded.computed_fingerprint != pin.fingerprint:
        reasons.append("computed_fingerprint_mismatch_against_pin")
    if manifest.dataset_version != pin.dataset_version:
        reasons.append(
            "dataset_version_mismatch:"
            f"manifest={manifest.dataset_version!r},pin={pin.dataset_version!r}"
        )
    if pin.source_package is not None:
        if manifest.source_package != pin.source_package:
            reasons.append(
                "source_package_mismatch:"
                f"manifest={manifest.source_package!r},pin={pin.source_package!r}"
            )

    if reasons:
        raise CorpusPinError(
            f"Corpus pin verification failed for {pin.corpus_id!r}: "
            + ", ".join(reasons)
        )


def resolve_pin_location(
    pin: CorpusPin,
    *,
    search_roots: Sequence[Path | str] = (),
    location_overrides: Mapping[str, Path | str] | None = None,
    explicit_path: Path | str | None = None,
) -> Path:
    """
    Resolve filesystem location for a pin.

    Precedence:
    1. ``explicit_path`` (caller-provided override)
    2. ``location_overrides[corpus_id]``
    3. ``search_roots`` / ``location_hint``
    """
    if explicit_path is not None:
        path = Path(explicit_path)
        if not str(explicit_path).strip():
            raise CorpusPinError("explicit_path must be non-empty when provided.")
        if not path.exists():
            raise CorpusLoadError(f"Pinned corpus path does not exist: {path}")
        if not path.is_dir():
            raise CorpusLoadError(f"Pinned corpus path is not a directory: {path}")
        return path.resolve()

    overrides = location_overrides or {}
    if pin.corpus_id in overrides:
        path = Path(overrides[pin.corpus_id])
        if not path.exists():
            raise CorpusLoadError(
                f"Pinned corpus override path does not exist for "
                f"{pin.corpus_id!r}: {path}"
            )
        if not path.is_dir():
            raise CorpusLoadError(
                f"Pinned corpus override path is not a directory for "
                f"{pin.corpus_id!r}: {path}"
            )
        return path.resolve()

    hint = pin.location_hint
    if hint is None:
        raise CorpusPinError(
            f"Corpus pin {pin.corpus_id!r} has no location_hint and no "
            "location override or explicit path was provided."
        )

    roots = tuple(Path(root) for root in search_roots if str(root).strip())
    if not roots:
        raise CorpusPinError(
            f"Corpus pin {pin.corpus_id!r} requires search_roots to resolve "
            f"location_hint={hint!r}."
        )

    candidates = [root / hint for root in roots]
    existing = [path for path in candidates if path.is_dir()]
    if not existing:
        searched = ", ".join(str(path) for path in candidates)
        raise CorpusLoadError(
            f"Pinned corpus {pin.corpus_id!r} not found under search roots. "
            f"Tried: {searched}"
        )
    if len(existing) > 1:
        raise CorpusPinError(
            f"Ambiguous location for corpus pin {pin.corpus_id!r}: "
            + ", ".join(str(path) for path in existing)
        )
    return existing[0].resolve()


__all__ = [
    "CorpusPin",
    "resolve_pin_location",
    "verify_loaded_corpus_against_pin",
]
