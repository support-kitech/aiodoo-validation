"""Configurable evaluation corpus provider (E5)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aiodoo_validation.corpus.exceptions import CorpusLoadError
from aiodoo_validation.corpus.gates import GatePurpose
from aiodoo_validation.corpus.loader import JsonlCorpusLoader, LoadedCorpus

# Request / plan configuration key for evaluation corpora.
EVALUATION_CORPUS_PATH_KEY = "evaluation_corpus_path"


@dataclass(frozen=True, slots=True)
class ConfigurableCorpusProvider:
    """
    Load evaluation corpora from configured paths.

    - Missing / empty path → ``None`` (caller defers behavioral evaluation)
    - Invalid path / gate failure → raises (fail closed; never silent defer)
    """

    loader: JsonlCorpusLoader = JsonlCorpusLoader()

    def resolve_path(self, configured: object | None) -> Path | None:
        if configured is None:
            return None
        if not isinstance(configured, (str, Path)):
            raise CorpusLoadError(
                f"{EVALUATION_CORPUS_PATH_KEY} must be a string path when set."
            )
        text = str(configured).strip()
        if not text:
            return None
        return Path(text)

    def load(
        self,
        configured_path: object | None,
        *,
        purpose: GatePurpose = "production_behavior",
    ) -> LoadedCorpus | None:
        path = self.resolve_path(configured_path)
        if path is None:
            return None
        return self.loader.load(path, purpose=purpose)


__all__ = [
    "EVALUATION_CORPUS_PATH_KEY",
    "ConfigurableCorpusProvider",
]
