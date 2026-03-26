# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    certificate_request_id = fields.Many2one(
        'irg.certificate.request',
        string='Solicitud de Certificado',
        copy=False,
        index=True,
    )

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            cert = order.certificate_request_id
            if cert and cert.state == 'pending_payment':
                # sudo() needed: the order may be confirmed in a portal context
                # where the cert record belongs to internal models
                cert.sudo()._process_payment()
        return res
