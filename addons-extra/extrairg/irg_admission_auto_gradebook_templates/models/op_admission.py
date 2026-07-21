# -*- coding: utf-8 -*-
import logging
import re
import unicodedata

from odoo import models

_logger = logging.getLogger(__name__)

_MASTER_NAME_RE = re.compile(r'(?:^| - )masters?(?:\s|$)')
_DIPLOMA_XMLID = (
    'irg_diploma_gradebook_template_weighting.gradebook_diploma_exam_50_50'
)
_MASTER_XMLID = (
    'irg_admission_auto_gradebook_templates.gradebook_master_solo_examen'
)
_MASTER_TEMPLATE_NAME = 'Solo Examen'


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def enroll_student(self):
        super().enroll_student()
        self._irg_assign_auto_gradebook_templates()

    def _irg_assign_auto_gradebook_templates(self):
        """Fill empty student gradebook templates after auto-creation."""
        GradebookStudent = self.env['app.gradebook.student'].sudo()
        for record in self:
            if record.state != 'done':
                continue
            gradebook = GradebookStudent.search(
                [('admission_id', '=', record.id)], limit=1
            )
            if not gradebook or gradebook.gradebook_id:
                continue

            template = record._irg_resolve_auto_gradebook_template(gradebook)
            if not template:
                continue

            gradebook.write({'gradebook_id': template.id})
            _logger.info(
                'IRG Auto Gradebook Templates: plantilla %s asignada a '
                'libreta %s (admisión %s).',
                template.display_name,
                gradebook.id,
                record.id,
            )

    def _irg_resolve_auto_gradebook_template(self, gradebook):
        """Return canonical template for empty gradebooks, or empty recordset."""
        self.ensure_one()
        if gradebook._is_diplomado_course():
            return self.env.ref(_DIPLOMA_XMLID, raise_if_not_found=False)

        course = gradebook.course_id or self.course_id
        if course and self._irg_is_master_course(course):
            return self._irg_get_master_solo_examen_template()

        return self.env['app.gradebook']

    def _irg_get_master_solo_examen_template(self):
        template = self.env.ref(_MASTER_XMLID, raise_if_not_found=False)
        if template:
            return template
        return self.env['app.gradebook'].sudo().search(
            [('name', '=', _MASTER_TEMPLATE_NAME)], limit=1
        )

    def _irg_is_master_course(self, course):
        self.ensure_one()
        if not course:
            return False

        if 'course_type_id' in course._fields and course.course_type_id:
            course_type = course.course_type_id
            if self._irg_is_master_label(
                self._irg_normalize_text(course_type.name)
            ):
                return True
            if self._irg_is_master_code(
                self._irg_normalize_text(course_type.code)
            ):
                return True

        return bool(_MASTER_NAME_RE.search(
            self._irg_normalize_text(course.name)
        ))

    @staticmethod
    def _irg_is_master_label(value):
        return (
            value in ('master', 'masters', 'masteres')
            or value.startswith('master ')
            or value.startswith('masters ')
        )

    @staticmethod
    def _irg_is_master_code(value):
        return value.startswith('mst') or value.startswith('master')

    @staticmethod
    def _irg_normalize_text(value):
        if not value:
            return ''
        normalized = unicodedata.normalize('NFKD', value)
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        normalized = normalized.lower()
        return re.sub(r'\s+', ' ', normalized).strip()
