"""CLI configuration (Phase 10)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CliConfig:
    """Immutable CLI runtime configuration."""

    program_name: str = "aiodoo-validation"
    debug: bool = False

    @classmethod
    def from_env(cls) -> CliConfig:
        debug = os.environ.get("AIODOO_VALIDATION_DEBUG", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(debug=debug)
