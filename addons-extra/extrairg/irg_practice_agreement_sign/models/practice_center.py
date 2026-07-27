# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PracticeCenter(models.Model):
    _inherit = 'practice.center'

    agreement_ids = fields.One2many(
        'practice.agreement',
        'practice_center_id',
        string='Convenios Marco'
    )
    agreement_count = fields.Integer(
        string='Nº Convenios',
        compute='_compute_agreement_count'
    )

    @api.depends('agreement_ids')
    def _compute_agreement_count(self):
        for record in self:
            record.agreement_count = len(record.agreement_ids)

    def action_create_agreement(self):
        """Crea un nuevo convenio en borrador pre-cumplimentado para este centro de prácticas."""
        self.ensure_one()
        agreement = self.env['practice.agreement'].create({
            'practice_center_id': self.id,
            'center_official_name': self.official_name or self.name,
            'signatory_name': self.signatory_name or self.coordinator,
            'street': self.street,
            'city': self.city,
            'zip': self.postal_code,
            'state_id': self.state_id.id if self.state_id else False,
            'country_id': self.country_id.id if self.country_id else False,
            'phone': self.phone or self.mobil,
            'email': self.email,
            'center_vat': self.partner_id.vat if self.partner_id else False,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Convenio Marco de Prácticas'),
            'res_model': 'practice.agreement',
            'res_id': agreement.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_agreements(self):
        """Abre la lista/formulario de convenios del centro de prácticas."""
        self.ensure_one()
        action = self.env.ref('irg_practice_agreement_sign.action_practice_agreement').read()[0]
        if len(self.agreement_ids) == 1:
            action['views'] = [(self.env.ref('irg_practice_agreement_sign.view_practice_agreement_form').id, 'form')]
            action['res_id'] = self.agreement_ids.id
        else:
            action['domain'] = [('practice_center_id', '=', self.id)]
        action['context'] = {'default_practice_center_id': self.id}
        return action
