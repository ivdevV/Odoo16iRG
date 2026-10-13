# -*- coding: utf-8 -*-
from odoo import fields, models

from odoo.addons.irg_practice_center_cif.cif import resolve_center_cif


class PracticeCenter(models.Model):
    _inherit = 'practice.center'

    cif = fields.Char(
        string='CIF',
        tracking=True,
        help='CIF del centro de prácticas.',
    )

    def _irg_resolved_cif(self):
        self.ensure_one()
        partner_vat = self.partner_id.vat if self.partner_id else False
        return resolve_center_cif(self.cif, partner_vat)

    def create_res_partner(self):
        result = super().create_res_partner()
        for center in self:
            partner = center.partner_id
            if not partner:
                continue
            vals = {}
            cif = resolve_center_cif(center.cif, False)
            if cif:
                vals['vat'] = cif
            if center.country_id and not partner.country_id:
                vals['country_id'] = center.country_id.id
            if vals:
                # El CIF del centro es texto libre. base_vat rechaza un NIF
                # sin país o con un formato que no reconoce y revertiría
                # la creación del contacto.
                partner.with_context(no_vat_validation=True).write(vals)
        return result

    def action_create_agreement(self):
        self.ensure_one()
        action = super().action_create_agreement()
        res_id = action.get('res_id')
        if res_id:
            resolved = self._irg_resolved_cif()
            if resolved:
                self.env['practice.agreement'].browse(res_id).center_vat = resolved
        return action
