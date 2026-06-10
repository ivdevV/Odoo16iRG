# -*- coding: utf-8 -*-

from odoo import _, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    academic_request_count = fields.Integer(
        string='Solicitudes Academicas',
        compute='_compute_academic_request_count',
    )

    def _compute_academic_request_count(self):
        Request = self.env['irg.certificate.request'].sudo()
        for partner in self:
            partner.academic_request_count = Request.search_count([
                ('partner_id', '=', partner.id),
            ])

    def action_view_academic_requests(self):
        self.ensure_one()
        action = self.env.ref(
            'irg_gradebook_certificates.action_irg_certificate_request'
        ).sudo().read()[0]
        action.update({
            'name': _('Solicitudes Academicas'),
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
            },
        })
        return action
