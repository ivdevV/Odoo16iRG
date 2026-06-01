# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class OpAdmissionRegister(models.Model):
    _inherit = 'op.admission.register'

    @api.model_create_multi
    def create(self, vals_list):
        """Override to align start_date and end_date to natural quarter boundaries

        upon creation for academic courses (excluding diplomados).
        """
        for vals in vals_list:
            period = vals.get('period')
            course_id = vals.get('course_id')
            if period and course_id:
                parts = period.split('-')
                if len(parts) == 2 and len(parts[0]) == 4 and parts[1] in ('01', '02', '03', '04'):
                    year = parts[0]
                    quarter_code = parts[1]
                    course = self.env['op.course'].browse(course_id)
                    if course:
                        is_academic = (
                            (course.product_template_id and course.product_template_id.is_academic_program) or
                            any(p.is_academic_program for p in course.product_template_ids)
                        )
                        if is_academic:
                            categ_code = (course.product_template_id.categ_id.code or '') if course.product_template_id.categ_id else ''
                            if not categ_code and hasattr(course, 'product_template_ids') and course.product_template_ids:
                                first_pt = course.product_template_ids[0]
                                categ_code = (first_pt.categ_id.code or '') if first_pt.categ_id else ''
                            if categ_code and categ_code.upper().startswith('DI'):
                                is_academic = False

                        if is_academic:
                            mapping = {
                                '01': ('01-01', '03-31'),
                                '02': ('04-01', '06-30'),
                                '03': ('07-01', '09-30'),
                                '04': ('10-01', '12-31'),
                            }
                            start_suffix, end_suffix = mapping[quarter_code]
                            vals['start_date'] = f"{year}-{start_suffix}"
                            vals['end_date'] = f"{year}-{end_suffix}"
                            _logger.info(
                                "IRG Quarterly Admission Registers: Setting quarterly dates %s to %s for created register with period %s",
                                vals['start_date'], vals['end_date'], period
                            )
        return super(OpAdmissionRegister, self).create(vals_list)

    def write(self, vals):
        """Override to align start_date and end_date to natural quarter boundaries

        upon update for academic courses (excluding diplomados).
        """
        res = super(OpAdmissionRegister, self).write(vals)
        for record in self:
            period = record.period
            course = record.course_id
            if period and course:
                parts = period.split('-')
                if len(parts) == 2 and len(parts[0]) == 4 and parts[1] in ('01', '02', '03', '04'):
                    year = parts[0]
                    quarter_code = parts[1]
                    is_academic = (
                        (course.product_template_id and course.product_template_id.is_academic_program) or
                        any(p.is_academic_program for p in course.product_template_ids)
                    )
                    if is_academic:
                        categ_code = (course.product_template_id.categ_id.code or '') if course.product_template_id.categ_id else ''
                        if not categ_code and hasattr(course, 'product_template_ids') and course.product_template_ids:
                            first_pt = course.product_template_ids[0]
                            categ_code = (first_pt.categ_id.code or '') if first_pt.categ_id else ''
                        if categ_code and categ_code.upper().startswith('DI'):
                            is_academic = False

                    if is_academic:
                        mapping = {
                            '01': ('01-01', '03-31'),
                            '02': ('04-01', '06-30'),
                            '03': ('07-01', '09-30'),
                            '04': ('10-01', '12-31'),
                        }
                        start_suffix, end_suffix = mapping[quarter_code]
                        expected_start = fields.Date.to_date(f"{year}-{start_suffix}")
                        expected_end = fields.Date.to_date(f"{year}-{end_suffix}")

                        write_vals = {}
                        if record.start_date != expected_start:
                            write_vals['start_date'] = expected_start
                        if record.end_date != expected_end:
                            write_vals['end_date'] = expected_end

                        if write_vals:
                            _logger.info(
                                "IRG Quarterly Admission Registers: Updating quarterly dates %s to %s for register ID %s with period %s",
                                write_vals.get('start_date', record.start_date),
                                write_vals.get('end_date', record.end_date),
                                record.id,
                                period
                            )
                            super(OpAdmissionRegister, record).write(write_vals)
        return res
