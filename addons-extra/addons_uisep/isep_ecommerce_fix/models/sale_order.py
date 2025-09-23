# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def get_academic_product_template_id(self):
        for record in self:
            error_admission_msn = []
            order_line = self.order_line.filtered(
                lambda x: x.product_template_id.is_academic_program and x.product_template_id.recurring_invoice
            )

            if order_line:
                for line in order_line:
                    if line.product_template_id.is_tesis:
                        continue

                    course_id = self.env['op.course'].search(
                        [('product_template_id', '=', line.product_template_id.id)],
                        limit=1
                    )

                    if course_id:
                        record.product_template_id = course_id.product_template_id
                        record.course_id = course_id.id
                    else:
                        error_admission_msn.append(
                            "* El programa académico %s debe asociarse con el cursos, comunícate con un asesor." % line.product_template_id.name
                        )

            if error_admission_msn:
                record.error_admission_msn = '\n'.join(error_admission_msn)
                record.error_admission = True
            else:
                record.error_admission_msn = False
                record.error_admission = False

    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        if self.recurrence_id and not self.subscription_schedule:
            self.create_subscription_schedule()

        order_line = self.order_line.filtered(
            lambda x: x.product_template_id.is_academic_program and x.product_template_id.recurring_invoice
        )
        has_tesis = any(order_line.mapped('product_template_id.is_tesis'))
        if not has_tesis:
            if order_line and not self.website_send_mail and self.is_from_website_origin:
                self.send_automated_action()
                self.website_send_mail = True

        return res

