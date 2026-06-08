# -*- coding: utf-8 -*-
import logging
from datetime import date as date_cls

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
        if line.order_id and line.order_id.course_id:
            course = line.order_id.course_id
            if self._irg_line_matches_course(line, course):
                return True
        course_domain = [('product_template_id', '=', pt.id)]
        if 'product_template_ids' in self.env['op.course']._fields:
            course_domain = ['|'] + course_domain + [('product_template_ids', 'in', [pt.id])]
        if self.env['op.course'].search_count([
            *course_domain,
        ]) > 0:
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

    def _irg_diplomado_batch_code(self, course, base_date):
        start_date, _end_date = self._irg_diplomado_fixed_dates(base_date)
        return 'DI%sHC%s09' % ((course.code or ''), start_date.strftime('%y'))

    def _get_line_modality(self, line):
        if line:
            course = line.order_id.course_id if line.order_id and self._irg_line_matches_course(line, line.order_id.course_id) else False
            if not course:
                course_domain = [('product_template_id', '=', line.product_template_id.id)]
                if 'product_template_ids' in self.env['op.course']._fields:
                    course_domain = ['|'] + course_domain + [('product_template_ids', 'in', [line.product_template_id.id])]
                course = self.env['op.course'].search(course_domain, limit=1)
            if self._irg_is_diplomado_line(line, course):
                return 'GE'
        return super()._get_line_modality(line)

    def get_lot_id(self, course_id):
        line_id = self.env.context.get('irg_get_lot_line_id')
        line = self.env['sale.order.line'].browse(line_id).exists() if line_id else False

        if not line:
            for candidate in self.order_line:
                pt = candidate.product_template_id
                if not pt:
                    continue
                if course_id.product_template_id and pt == course_id.product_template_id:
                    line = candidate
                    break
                if 'product_template_ids' in course_id._fields and pt in course_id.product_template_ids:
                    line = candidate
                    break

        if not self._irg_is_diplomado_line(line, course_id):
            return super().get_lot_id(course_id)

        base_date = (line and line.start_date_enroller) or self.admission_date or fields.Date.today()
        batch_start_date, batch_end_date = self._irg_diplomado_fixed_dates(base_date)
        code = self._irg_diplomado_batch_code(course_id, base_date)
        batch = self.env['op.batch'].search([('code', '=', code), ('course_id', '=', course_id.id)], limit=1)
        if batch:
            return batch

        values = {
            'name': code,
            'code': code,
            'course_id': course_id.id,
            'start_date': batch_start_date,
            'end_date': batch_end_date,
            'date_start_class': batch_start_date,
        }

        ad = self.env['auto.admission.required'].search([], limit=1)
        if ad:
            if course_id.lang == 'pt_BR':
                values.update({
                    'tutor_id': ad.br_tutor_id.id if ad.br_tutor_id else False,
                    'professor_id': ad.br_professor_id.id if ad.br_professor_id else False,
                    'coordinator': ad.br_coordinator.id if ad.br_coordinator else False,
                    'teams_domain': ad.br_teams_domain or False,
                    'teams_link': ad.br_teams_link or False,
                    'teams_msg': ad.br_teams_msg or False,
                    'modality_id': ad.br_modality_id.id if ad.br_modality_id else False,
                })
            else:
                values.update({
                    'tutor_id': ad.mx_tutor_id.id if ad.mx_tutor_id else False,
                    'professor_id': ad.mx_professor_id.id if ad.mx_professor_id else False,
                    'coordinator': ad.mx_coordinator.id if ad.mx_coordinator else False,
                    'teams_domain': ad.mx_teams_domain or False,
                    'teams_link': ad.mx_teams_link or False,
                    'teams_msg': ad.mx_teams_msg or False,
                    'modality_id': ad.mx_modality_id.id if ad.mx_modality_id else False,
                })

        hc_modality = self.env['op.modality'].search([('name', '=ilike', 'HomeClass')], limit=1)
        if hc_modality:
            values['modality_id'] = hc_modality.id

        _logger.info('IRG Diplomado Fixed Batch: creating fixed annual batch %s with values %s', code, values)
        return self.env['op.batch'].create(values)
