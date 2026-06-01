# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('admission_date', 'order_line.product_template_id.is_academic_program')
    def _compute_period(self):
        """Override to compute a natural quarterly calendar format (Q1-Q4)

        if the sale order contains academic lines (excluding diplomados).
        """
        super(SaleOrder, self)._compute_period()
        for record in self:
            academic_lines = record.order_line.filtered(
                lambda l: l.product_template_id.is_academic_program and not (
                    l.product_template_id.categ_id and (
                        l.product_template_id.categ_id.code or ''
                    ).upper().startswith('DI')
                )
            )
            if academic_lines and record.admission_date:
                year = record.admission_date.year
                month = record.admission_date.month
                if month in (1, 2, 3):
                    quarter_code = '01'
                elif month in (4, 5, 6):
                    quarter_code = '02'
                elif month in (7, 8, 9):
                    quarter_code = '03'
                else:  # 10, 11, 12
                    quarter_code = '04'
                record.period = f"{year}-{quarter_code}"

    def _find_or_create_register(self, *, period, product_template, course):
        """Override to use the quarterly calendar format for academic programs

        (excluding diplomados) based on the line's start date (with fallbacks).
        """
        line_id = self.env.context.get('irg_get_lot_line_id')
        line = self.env['sale.order.line'].browse(line_id) if line_id else self.env['sale.order.line']

        is_academic = False
        if line and line.product_template_id.is_academic_program:
            is_academic = True
        elif any(l.product_template_id.is_academic_program for l in self.order_line):
            is_academic = True

        # Exclude diplomados (category code starts with 'DI')
        if is_academic:
            if line:
                categ_code = (line.product_template_id.categ_id.code or '') if line.product_template_id.categ_id else ''
                if categ_code.upper().startswith('DI'):
                    is_academic = False
            if is_academic and course:
                categ_code = (course.product_template_id.categ_id.code or '') if course.product_template_id.categ_id else ''
                if not categ_code and hasattr(course, 'product_template_ids') and course.product_template_ids:
                    first_pt = course.product_template_ids[0]
                    categ_code = (first_pt.categ_id.code or '') if first_pt.categ_id else ''
                if categ_code.upper().startswith('DI'):
                    is_academic = False

        if is_academic:
            line_date = line.start_date_enroller if line else False
            if not line_date:
                line_date = self.admission_date
            if not line_date:
                line_date = fields.Date.today()

            # Apply modality shift logic to align with irg_sale_manual_confirmation_wizard
            if line:
                modality = self._get_line_modality(line) if hasattr(self, '_get_line_modality') else ''
                today = fields.Date.today()
                if modality in ('HC', 'PRS') and today.day > 7 and line_date.month == today.month and line_date.year == today.year:
                    from dateutil.relativedelta import relativedelta
                    line_date = line_date + relativedelta(months=1)

                if modality == 'HC':
                    if line_date.month in (7, 8) or (line_date.month == 9 and line_date.day == 1):
                        line_date = line_date.replace(month=9, day=1)

            year = line_date.year
            month = line_date.month
            if month in (1, 2, 3):
                quarter_code = '01'
            elif month in (4, 5, 6):
                quarter_code = '02'
            elif month in (7, 8, 9):
                quarter_code = '03'
            else:  # 10, 11, 12
                quarter_code = '04'
            period = f"{year}-{quarter_code}"
            _logger.info(
                "IRG Quarterly Admission Registers: Overriding period to %s for course %s",
                period, course.name
            )

            # Clear context flag during super() call to prevent irg_sale_manual_confirmation_wizard
            # from overwriting the computed quarterly period parameter.
            self = self.with_context(irg_get_lot_line_id=False)

        return super(SaleOrder, self)._find_or_create_register(
            period=period,
            product_template=product_template,
            course=course
        )

    def gat_date_max_register(self, periodo):
        """Override to return the last day of the corresponding natural quarter

        if the order contains any academic line that is NOT a diplomado.
        """
        has_academic = any(
            l.product_template_id.is_academic_program and not (
                l.product_template_id.categ_id and (
                    l.product_template_id.categ_id.code or ''
                ).upper().startswith('DI')
            )
            for l in self.order_line
        )
        if has_academic:
            try:
                parts = periodo.split('-')
                if len(parts) == 2:
                    year, quarter_code = parts
                    mapping = {
                        '01': '03-31',
                        '02': '06-30',
                        '03': '09-30',
                        '04': '12-31',
                    }
                    if quarter_code in mapping:
                        date_str = f"{year}-{mapping[quarter_code]}"
                        return datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception as e:
                _logger.warning(
                    "Error parsing period %s in gat_date_max_register: %s. Falling back to super.",
                    periodo, e
                )
        return super(SaleOrder, self).gat_date_max_register(periodo)
