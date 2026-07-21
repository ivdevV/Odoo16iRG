# -*- coding: utf-8 -*-
import logging
import re
import unicodedata

from odoo import api, models

_logger = logging.getLogger(__name__)

_MASTER_NAME_RE = re.compile(r'(?:^| - )masters?(?:\s|$)')
_DIPLOMA_XMLID = (
    'irg_diploma_gradebook_template_weighting.gradebook_diploma_exam_50_50'
)
_MASTER_XMLID = (
    'irg_admission_auto_gradebook_templates.gradebook_master_solo_examen'
)
_MASTER_TEMPLATE_NAME = 'Solo Examen'


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_assign_canonical_gradebook_template()
        return records

    def write(self, vals):
        res = super().write(vals)
        if (
            'admission_id' in vals
            and not self.env.context.get('irg_skip_canonical_template')
        ):
            self._irg_assign_canonical_gradebook_template()
        return res

    def _irg_assign_canonical_gradebook_template(self):
        """Fill empty gradebook_id from course or canonical master/diplomado.

        Solo escribe gradebook_id. No crea, borra ni modifica
        app.gradebook.result ni líneas de asignatura. Los promedios se
        recalculan por compute; irg_gradebook_partial_averages evita
        ponerlos a 0 cuando ya hay resultados.
        """
        if self.env.context.get('irg_skip_canonical_template'):
            return
        for record in self:
            if record.gradebook_id:
                continue
            template = record._irg_resolve_canonical_gradebook_template()
            if not template:
                continue
            # Evitar reentrada del write() por admission_id.
            record.with_context(
                irg_skip_canonical_template=True,
            ).write({'gradebook_id': template.id})
            _logger.info(
                'IRG Auto Gradebook Templates: plantilla %s asignada a '
                'libreta %s (admisión %s).',
                template.display_name,
                record.id,
                record.admission_id.id if record.admission_id else False,
            )

    def _irg_resolve_canonical_gradebook_template(self):
        self.ensure_one()
        if self.course_id and self.course_id.gradebook_id:
            return self.course_id.gradebook_id

        if self._is_diplomado_course():
            return self.env.ref(_DIPLOMA_XMLID, raise_if_not_found=False)

        if self.course_id and self._irg_is_master_course(self.course_id):
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
