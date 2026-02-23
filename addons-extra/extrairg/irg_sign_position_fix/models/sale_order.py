# -*- coding: utf-8 -*-

import base64
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class SaleOrderSignFix(models.Model):
    _inherit = 'sale.order'

    def action_send_to_sign(self):
        report_model = self.env['ir.actions.report']
        pdf = report_model._render_qweb_pdf(self.company_id.isep_prematricula_id.id, res_ids=self.id)
        pdf_content = base64.b64encode(pdf[0])
        fname = 'Matrícula ' + self.partner_id.name
        attach = self.env['ir.attachment'].create({
            'name': fname,
            'type': 'binary',
            'datas': pdf_content,
            'store_fname': fname + '.pdf',
            'res_model': 'sale.order',
            'res_id': self.id,
            'mimetype': 'application/pdf;base64'
        })
        if attach:
            sign = self.env['sign.template'].create({
                'attachment_id': attach.id,
                'favorited_ids': [(4, self.env.user.id)],
                'sale_id': self.id,
            })
            if sign:
                # determine sign positions from report helper so they track
                # the actual placement of the raimon signature image; the report
                # component must expose these values (same constants are used
                # when the image is drawn).
                sign_pages = report_model.get_raimon_signature_positions()
                # Use left margin for X position rather than hardcoded offset
                # assuming margin corresponds to 0.0 in page coordinates.
                if self.partner_id.id != self.partner_invoice_id.id:
                    for page, pos_y in sign_pages.items():
                        if page <= sign.num_pages:
                            self.env['sign.item'].create({
                                'template_id': sign.id,
                                'type_id': 1,
                                'required': True,
                                'responsible_id': 1,
                                'page': page,
                                'posX': 0.070,  # aligned with IRG signature position
                                'posY': pos_y,
                                'width': 0.165,
                                'height': 0.040,
                            })
                elif self.partner_id.id == self.partner_invoice_id.id:
                    for page, pos_y in sign_pages.items():
                        if page <= sign.num_pages:
                            self.env['sign.item'].create({
                                'template_id': sign.id,
                                'type_id': 1,
                                'required': True,
                                'responsible_id': 4,
                                'page': page,
                                'posX': 0.070,  # aligned with IRG signature position
                                'posY': pos_y,
                                'width': 0.165,
                                'height': 0.040,
                            })

                self.sign_id = sign.id
