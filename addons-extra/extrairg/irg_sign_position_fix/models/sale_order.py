# -*- coding: utf-8 -*-

import base64
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


# Normalized vertical positions (fraction of page height) where the raimon
# signature image appears in the prematrícula report.  Update these if the
# report layout changes.
RAIMON_SIGNATURE_POSITIONS = {
    1: 0.700,
    3: 0.650,
}


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
                sign_pages = RAIMON_SIGNATURE_POSITIONS
                if self.partner_id.id != self.partner_invoice_id.id:
                    for page, pos_y in sign_pages.items():
                        if page <= sign.num_pages:
                            self.env['sign.item'].create({
                                'template_id': sign.id,
                                'type_id': 1,
                                'required': True,
                                'responsible_id': 1,
                                'page': page,
                                'posX': 0.15,
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
                                'posX': 0.15,
                                'posY': pos_y,
                                'width': 0.165,
                                'height': 0.040,
                            })

                self.sign_id = sign.id
