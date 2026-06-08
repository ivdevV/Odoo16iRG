# -*- coding: utf-8 -*-
from datetime import date as date_cls

from odoo import fields, models


class ManualConfirmationWizard(models.TransientModel):
    _inherit = 'irg.manual.confirmation.wizard'

    def _irg_line_matches_course(self, line, course):
        pt = line.product_template_id if line else False
        if not pt or not course:
            return False
        if course.product_template_id and pt == course.product_template_id:
            return True
        return bool('product_template_ids' in course._fields and pt in course.product_template_ids)

    def _is_academic_line(self, line):
        pt = line.product_template_id
        if not pt:
            return False
        if pt.is_academic_program:
            return True
        order = line.order_id
        if order and order.course_id:
            if self._irg_line_matches_course(line, order.course_id):
                return True
        course_domain = [('product_template_id', '=', pt.id)]
        if 'product_template_ids' in self.env['op.course']._fields:
            course_domain = ['|'] + course_domain + [('product_template_ids', 'in', [pt.id])]
        if self.env['op.course'].search_count(course_domain) > 0:
            return True
        categ = pt.categ_id
        if categ:
            if categ.code and categ.code.upper().startswith('DI'):
                return True
            if categ.name and 'DIPLOMADO' in categ.name.upper():
                return True
        return bool(pt.name and 'DIPLOMADO' in pt.name.upper())

    def _irg_is_diplomado_line(self, line, course=False):
        pt = line.product_template_id if line else False
        categs = line.product_id.categ_id | pt.categ_id if line and pt else self.env['product.category']

        if course and self._irg_line_matches_course(line, course):
            if course.product_template_id and course.product_template_id.categ_id:
                categs |= course.product_template_id.categ_id
            if 'product_template_ids' in course._fields and course.product_template_ids:
                categs |= course.product_template_ids.mapped('categ_id')

        for categ in categs:
            code = (categ.code or '').strip().upper()
            name = (categ.name or '').strip().upper()
            if code.startswith('DI') or code == 'D' or 'DIPLOMADO' in name:
                return True

        return bool(pt and pt.name and 'DIPLOMADO' in pt.name.upper())

    def _irg_diplomado_fixed_dates(self, base_date):
        base_date = base_date or fields.Date.today()
        return date_cls(base_date.year, 6, 28), date_cls(base_date.year, 9, 30)

    def _detect_line_modalidad(self, line, course_id):
        if self._irg_is_diplomado_line(line, course_id):
            return 'Diplomado'
        return super()._detect_line_modalidad(line, course_id)

    def _find_course_for_line(self, line):
        if line.order_id and self._irg_line_matches_course(line, line.order_id.course_id):
            return line.order_id.course_id
        course_domain = [('product_template_id', '=', line.product_template_id.id)]
        if 'product_template_ids' in self.env['op.course']._fields:
            course_domain = ['|'] + course_domain + [('product_template_ids', 'in', [line.product_template_id.id])]
        return self.env['op.course'].search(course_domain, limit=1)

    def _build_line_batch_code_preview(self, line, course_id, modality, date):
        if course_id and self._irg_is_diplomado_line(line, course_id):
            start_date, _end_date = self._irg_diplomado_fixed_dates(date)
            return 'DI%sHC%s06' % ((course_id.code or ''), start_date.strftime('%y'))
        return super()._build_line_batch_code_preview(line, course_id, modality, date)
