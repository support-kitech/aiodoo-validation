"""Report template registry (Phase 9)."""

from __future__ import annotations

from dataclasses import dataclass, field

from aiodoo_validation.domain.enums import ReportErrorCode
from aiodoo_validation.domain.report import ReportError
from aiodoo_validation.reporting.base import ReportTemplate
from aiodoo_validation.reporting.templates import default_coding_placeholder_templates


@dataclass
class ReportRegistry:
    """
    Register and resolve report templates by ID.

    Supports future plugins and additional profiles without engine changes.
    """

    _templates: dict[str, ReportTemplate] = field(default_factory=dict)

    @classmethod
    def create_default(cls) -> ReportRegistry:
        registry = cls()
        for template in default_coding_placeholder_templates():
            registry.register(template)
        return registry

    def register(self, template: ReportTemplate) -> None:
        template_id = template.metadata.template_id
        if not template_id:
            raise ReportError(
                code=ReportErrorCode.REGISTRATION_FAILURE,
                message="Report template metadata must include a non-empty template_id.",
                field="template_id",
            )
        if template_id in self._templates:
            raise ReportError(
                code=ReportErrorCode.REGISTRATION_FAILURE,
                message=f"Report template {template_id!r} is already registered.",
                field="template_id",
                template_id=template_id,
            )
        self._templates[template_id] = template

    def get(self, template_id: str) -> ReportTemplate:
        template = self._templates.get(template_id)
        if template is None:
            raise ReportError(
                code=ReportErrorCode.TEMPLATE_NOT_FOUND,
                message=f"Report template {template_id!r} is not registered.",
                field="template_id",
                template_id=template_id,
            )
        return template

    def resolve(self, template_id: str) -> ReportTemplate | None:
        return self._templates.get(template_id)

    def contains(self, template_id: str) -> bool:
        return template_id in self._templates

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._templates))
