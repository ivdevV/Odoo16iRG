# -*- coding: utf-8 -*-
import logging
import re
import unicodedata

from odoo import api, fields, models

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

    gradebook_id = fields.Many2one(
        'app.gradebook',
        string='Calificaciones template',
        store=True,
        compute='compute_gradebook_id',
        readonly=False,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_assign_canonical_gradebook_template()
        return records

    def write(self, vals):
        vals = dict(vals)
        force_template = self.env.context.get('irg_force_gradebook_template')
        if 'gradebook_id' in vals and not force_template:
            protected = self.filtered(lambda r: r._irg_has_existing_grades())
            if protected:
                _logger.info(
                    'IRG Auto Gradebook Templates: no se cambia gradebook_id '
                    'en libreta(s) %s porque ya hay notas registradas.',
                    protected.ids,
                )
                if protected == self:
                    vals.pop('gradebook_id', None)
                else:
                    # Multi-write mixto: aplicar plantilla solo a las sin notas.
                    other_vals = dict(vals)
                    vals_without_template = {
                        key: value for key, value in vals.items()
                        if key != 'gradebook_id'
                    }
                    res = True
                    writable = self - protected
                    if writable:
                        res = super(AppGradebookStudent, writable).write(
                            other_vals
                        )
                    if vals_without_template:
                        res = super(AppGradebookStudent, protected).write(
                            vals_without_template
                        ) and res
                    if (
                        'admission_id' in vals
                        and not self.env.context.get(
                            'irg_skip_canonical_template'
                        )
                    ):
                        writable._irg_assign_canonical_gradebook_template()
                    return res

        res = super().write(vals)
        if (
            'admission_id' in vals
            and not self.env.context.get('irg_skip_canonical_template')
        ):
            self._irg_assign_canonical_gradebook_template()
        return res

    @api.depends('course_id')
    def compute_gradebook_id(self):
        """No adoptar plantilla del curso si la libreta ya tiene notas."""
        for rec in self:
            if rec._irg_has_existing_grades():
                rec.gradebook_id = rec.gradebook_id
            else:
                rec.gradebook_id = rec.gradebook_id or rec.course_id.gradebook_id

    def _irg_has_existing_grades(self):
        """True si hay al menos un resultado de calificación en la libreta."""
        self.ensure_one()
        return bool(self.gradebook_subject_ids.gradebook_result_ids)

    def _irg_assign_canonical_gradebook_template(self):
        """Rellena gradebook_id vacío salvo que ya existan notas.

        Si hay resultados, no escribe nada (ni plantilla ni otros campos)
        para evitar recomputes que alteren promedios/notas visibles.
        """
        if self.env.context.get('irg_skip_canonical_template'):
            return
        for record in self:
            if record.gradebook_id:
                continue
            if record._irg_has_existing_grades():
                _logger.info(
                    'IRG Auto Gradebook Templates: omitida asignación de '
                    'plantilla en libreta %s (ya hay notas).',
                    record.id,
                )
                continue
            template = record._irg_resolve_canonical_gradebook_template()
            if not template:
                continue
            record.with_context(
                irg_skip_canonical_template=True,
                irg_force_gradebook_template=True,
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
