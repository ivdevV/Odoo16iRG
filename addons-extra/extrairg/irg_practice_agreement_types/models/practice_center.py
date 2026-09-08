# -*- coding: utf-8 -*-

from odoo import models, _


class PracticeCenter(models.Model):
    _inherit = 'practice.center'

    def action_open_create_agreement_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crear Convenio'),
            'res_model': 'irg.practice.agreement.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_practice_center_id': self.id,
            },
        }
