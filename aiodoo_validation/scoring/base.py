"""Scoring policy protocol."""

from __future__ import annotations

from typing import Protocol

from aiodoo_validation.domain.scoring import ScoreContext, ScoreMetadata, ScoreResult


class ScorePolicy(Protocol):
    """
    Contract for a scoring policy.

    Policies consume OracleResult values only — never inspect source files.
    """

    @property
    def metadata(self) -> ScoreMetadata: ...

    def score(self, context: ScoreContext) -> ScoreResult: ...
