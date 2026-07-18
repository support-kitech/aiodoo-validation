"""Certification Engine package (Phase 8 / E8 behavior gates)."""

from aiodoo_validation.certification.base import CertificationPolicy
from aiodoo_validation.certification.behavioral import BehaviorGatedCertificationPolicy
from aiodoo_validation.certification.criteria import (
    CertificationCriteria,
    CriteriaEvaluation,
    default_behavior_gated_certification_criteria,
    default_structural_certification_criteria,
    evaluate_certification_criteria,
)
from aiodoo_validation.certification.engine import CertificationEngine
from aiodoo_validation.certification.policies import (
    ManifestCertificationPolicy,
    MetadataCertificationPolicy,
    ModuleStructureCertificationPolicy,
    PlaceholderCertificationPolicy,
    PythonCertificationPolicy,
    QualityCertificationPolicy,
    SecurityCertificationPolicy,
    XmlCertificationPolicy,
)
from aiodoo_validation.certification.registry import CertificationRegistry

__all__ = [
    "BehaviorGatedCertificationPolicy",
    "CertificationCriteria",
    "CertificationEngine",
    "CertificationPolicy",
    "CertificationRegistry",
    "CriteriaEvaluation",
    "ManifestCertificationPolicy",
    "MetadataCertificationPolicy",
    "ModuleStructureCertificationPolicy",
    "PlaceholderCertificationPolicy",
    "PythonCertificationPolicy",
    "QualityCertificationPolicy",
    "SecurityCertificationPolicy",
    "XmlCertificationPolicy",
    "default_behavior_gated_certification_criteria",
    "default_structural_certification_criteria",
    "evaluate_certification_criteria",
]
