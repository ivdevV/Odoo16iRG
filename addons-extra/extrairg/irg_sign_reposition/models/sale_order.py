# -*- coding: utf-8 -*-
import base64
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrderSignReposition(models.Model):
    _inherit = 'sale.order'

    def action_send_to_sign(self):
        """
        Render the prematricula PDF, create an attachment and a `sign.template`
        with `sign.item` entries positioned to match IRG signature placement.
        This module provides an alternative implementation to adjust vertical
        positions (posY) and X offsets to 'subir' the signature box.
        """
        report = self.env['ir.actions.report']
        report_id = self.company_id.isep_prematricula_id.id
        pdf = report._render_qweb_pdf(report_id, res_ids=self.id)
        pdf_content = base64.b64encode(pdf[0])
        fname = 'Matrícula ' + (self.partner_id.name or 'document')
        attach = self.env['ir.attachment'].create({
            'name': fname,
            'type': 'binary',
            'datas': pdf_content,
            'store_fname': fname + '.pdf',
            'res_model': 'sale.order',
            'res_id': self.id,
            'mimetype': 'application/pdf;base64'
        })
        if not attach:
            _logger.warning('Could not create attachment for sale.order %s', self.id)
            return super(SaleOrderSignReposition, self).action_send_to_sign()

        sign = self.env['sign.template'].create({
            'attachment_id': attach.id,
            'favorited_ids': [(4, self.env.user.id)],
            'sale_id': self.id,
        })

        # Position map: pages -> posY (values tuned to 'subir bastante')
        # Adjust these numbers further after testing with real PDF output.
        sign_pages = {
            1: 0.750,  # move up on page 1
            3: 0.4500,  # move up on page 3
        }

        # Horizontal offsets depending on whether invoice partner equals partner
        for page, pos_y in sign_pages.items():
            if page <= sign.num_pages:
                pos_x = 0.70
                responsible = self.env.user.id
                self.env['sign.item'].create({
                    'template_id': sign.id,
                    'type_id': 1,
                    'required': True,
                    'responsible_id': responsible,
                    'page': page,
                    'posX': pos_x,
                    'posY': pos_y,
                    'width': 0.165,
                    'height': 0.040,
                })

        self.sign_id = sign.id
        return True
