# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    agreement_ids = fields.One2many(
        'practice.agreement',
        'practice_request_id',
        string='Convenios',
    )

    def action_open_create_specific_agreement_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crear Convenio'),
            'res_model': 'irg.practice.agreement.specific.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_practice_request_id': self.id,
                'default_agreement_type': 'especifico_internacional',
            },
        }
