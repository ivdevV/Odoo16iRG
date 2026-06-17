# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    certificate_request_ids = fields.One2many(
        'irg.certificate.request',
        'partner_id',
        string='Solicitudes de Certificados',
    )
    certificate_request_count = fields.Integer(
        string='Cantidad de Certificados',
        compute='_compute_certificate_request_count',
    )

    def _compute_certificate_request_count(self):
        for partner in self:
            partner.certificate_request_count = len(partner.certificate_request_ids)

    def action_view_certificate_requests(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('irg_gradebook_certificates.action_irg_certificate_request')
        action.update({
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        })
        return action
