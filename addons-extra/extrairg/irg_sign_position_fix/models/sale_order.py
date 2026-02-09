# -*- coding: utf-8 -*-

import base64
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class SaleOrderSignFix(models.Model):
    _inherit = 'sale.order'

    def action_send_to_sign(self):
        report = self.env['ir.actions.report']
        pdf = report._render_qweb_pdf(self.company_id.isep_prematricula_id.id, res_ids=self.id)
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
                if self.partner_id.id != self.partner_invoice_id.id:
                    for i in range(0, sign.num_pages):
                        self.env['sign.item'].create({
                            'template_id': sign.id,
                            'type_id': 1,
                            'required': True,
                            'responsible_id': 1,
                            'page': i + 1,
                            'posX': 0.420,
                            'posY': 0.280,
                            'width': 0.165,
                            'height': 0.040,
                        })
                elif self.partner_id.id == self.partner_invoice_id.id:
                    for i in range(0, sign.num_pages):
                        self.env['sign.item'].create({
                            'template_id': sign.id,
                            'type_id': 1,
                            'required': True,
                            'responsible_id': 4,
                            'page': i + 1,
                            'posX': 0.120,
                            'posY': 0.280,
                            'width': 0.165,
                            'height': 0.040,
                        })

                self.sign_id = sign.id
