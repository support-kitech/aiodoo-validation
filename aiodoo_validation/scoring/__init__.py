"""Scoring Engine package (Phase 6)."""

from aiodoo_validation.scoring.base import ScorePolicy
from aiodoo_validation.scoring.engine import ScoringEngine
from aiodoo_validation.scoring.policies import (
    ManifestScorePolicy,
    MetadataScorePolicy,
    ModuleStructureScorePolicy,
    PlaceholderScorePolicy,
    PythonScorePolicy,
    QualityScorePolicy,
    SecurityScorePolicy,
    XmlScorePolicy,
)
from aiodoo_validation.scoring.registry import ScoringRegistry

__all__ = [
    "ManifestScorePolicy",
    "MetadataScorePolicy",
    "ModuleStructureScorePolicy",
    "PlaceholderScorePolicy",
    "PythonScorePolicy",
    "QualityScorePolicy",
    "ScorePolicy",
    "ScoringEngine",
    "ScoringRegistry",
    "SecurityScorePolicy",
    "XmlScorePolicy",
]
