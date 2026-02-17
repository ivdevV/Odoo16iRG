from dateutil.relativedelta import relativedelta

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_lot_id(self, course_id):
        lot_id = super().get_lot_id(course_id)

        if lot_id:
            today = fields.Date.today()
            original_expected_end = today + relativedelta(years=1)
            new_expected_end = today + relativedelta(months=18)

            if not lot_id.end_date or lot_id.end_date == original_expected_end:
                lot_id.write({'end_date': new_expected_end})

        return lot_id
