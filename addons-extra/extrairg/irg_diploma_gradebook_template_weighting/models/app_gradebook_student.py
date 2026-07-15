# -*- coding: utf-8 -*-
import logging
import re
import unicodedata

from odoo import api, models


_logger = logging.getLogger(__name__)


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    @api.depends(
        'gradebook_id.final_calculation_mode',
        'course_id.name',
        'course_id.code',
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'course_id.product_template_id.categ_id.name',
        'course_id.product_template_id.categ_id.code',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.subject_type',
    )
    def _compute_diploma_recovery_required(self):
        return super()._compute_diploma_recovery_required()

    @api.depends(
        'gradebook_id.final_calculation_mode',
        'course_id.name',
        'course_id.code',
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'course_id.product_template_id.categ_id.name',
        'course_id.product_template_id.categ_id.code',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.subject_type',
        'diploma_recovery_required',
        'diploma_recovery_score',
        'diploma_recovery_applied',
    )
    def _amount_prod_final(self):
        return super()._amount_prod_final()

    @api.depends(
        'student_id',
        'gradebook_id.final_calculation_mode',
        'course_id.name',
        'course_id.code',
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'course_id.product_template_id.categ_id.name',
        'course_id.product_template_id.categ_id.code',
        'gradebook_subject_ids',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.subject_type',
        'diploma_recovery_required',
        'diploma_recovery_score',
        'diploma_recovery_applied',
    )
    def compute_avg_score(self):
        return super().compute_avg_score()

    def _get_diploma_weighting_values(self):
        """Return exact 50/50 values, or ``False`` to keep core behavior."""
        self.ensure_one()
        if not self.gradebook_id:
            return False
        if self.gradebook_id.final_calculation_mode != 'diploma_50_50':
            return False
        if not self._is_diplomado_course():
            return False

        compulsory_subjects = self.gradebook_subject_ids.filtered(
            lambda line: line.op_subject_id.subject_type == 'compulsory'
        )
        presencial_subjects = compulsory_subjects.filtered(
            lambda line: self._is_presential_module_subject(line)
        )
        if len(presencial_subjects) != 1:
            _logger.warning(
                'Diploma 50/50 skipped for gradebook %s: found %s '
                'presential subject candidates.',
                self.id,
                len(presencial_subjects),
            )
            return False

        non_presential_subjects = compulsory_subjects - presencial_subjects
        if not non_presential_subjects:
            _logger.warning(
                'Diploma 50/50 skipped for gradebook %s: no ordinary '
                'compulsory subjects found.',
                self.id,
            )
            return False

        presencial_score = presencial_subjects.final_subject_note
        non_presential_average = (
            sum(non_presential_subjects.mapped('final_subject_note'))
            / len(non_presential_subjects)
        )
        return {
            'base_final': (
                presencial_score * 0.5
                + non_presential_average * 0.5
            ),
            'presencial_score': presencial_score,
            'non_presential_average': non_presential_average,
            'non_presential_count': len(non_presential_subjects),
            'non_presential_weight': 50.0 / len(non_presential_subjects),
        }

    def _is_diplomado_course(self):
        self.ensure_one()
        course = self.course_id
        if not course:
            return False

        products = self.env['product.template']
        if 'product_template_id' in course._fields and course.product_template_id:
            products |= course.product_template_id
        if (
            'product_template_ids' in course._fields
            and course.product_template_ids
        ):
            products |= course.product_template_ids

        for category in products.mapped('categ_id'):
            category_name = self._normalize_text(category.name)
            category_code = self._normalize_text(
                getattr(category, 'code', '')
            )
            if self._is_diplomado_label(category_name):
                return True
            if self._is_diplomado_code(category_code):
                return True

        if products:
            # Product category is the primary structured classification. A
            # configured non-diploma product must not be overridden by a
            # marketing name or by an inconsistent course type.
            return False

        if 'course_type_id' in course._fields and course.course_type_id:
            course_type = course.course_type_id
            if self._is_diplomado_label(
                self._normalize_text(course_type.name)
            ):
                return True
            if self._is_diplomado_code(
                self._normalize_text(course_type.code)
            ):
                return True
            # A populated, non-diploma type is authoritative. The course name
            # is only a fallback when structured classification is absent.
            return False

        return self._is_diplomado_label(
            self._normalize_text(course.name)
        )

    def _is_presential_module_subject(self, gradebook_subject):
        subject_name = (
            gradebook_subject.op_subject_id.name
            or gradebook_subject.name
        )
        normalized_name = self._normalize_text(subject_name)
        return bool(re.search(
            r'(?:^| - )modulo presencial(?:\s*/\s*homeclass)?$',
            normalized_name,
        ))

    @staticmethod
    def _is_diplomado_code(value):
        return value == 'd' or value.startswith('di')

    @staticmethod
    def _is_diplomado_label(value):
        return (
            value in ('diplomado', 'diplomados')
            or value.startswith('diplomado ')
            or value.startswith('diplomados ')
        )

    @api.model
    def _normalize_text(self, value):
        if not value:
            return ''
        normalized = unicodedata.normalize('NFKD', value)
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        normalized = normalized.lower()
        return re.sub(r'\s+', ' ', normalized).strip()
