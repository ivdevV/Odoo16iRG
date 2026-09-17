# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PracticeAgreementCreateWizard(models.TransientModel):
    _name = 'irg.practice.agreement.create.wizard'
    _description = 'Crear Convenio'

    practice_center_id = fields.Many2one(
        'practice.center',
        string='Centro de Prácticas',
        required=True,
        ondelete='cascade',
    )
    agreement_type = fields.Selection(
        [
            ('marco_nacional', 'Convenio Marco Nacional'),
            ('marco_internacional', 'Convenio Marco Internacional'),
        ],
        string='Tipo de convenio',
        required=True,
        default='marco_nacional',
    )

    def action_create_agreement(self):
        self.ensure_one()
        agreement = self.env['practice.agreement'].create({
            'practice_center_id': self.practice_center_id.id,
            'agreement_type': self.agreement_type,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Convenio'),
            'res_model': 'practice.agreement',
            'res_id': agreement.id,
            'view_mode': 'form',
            'target': 'current',
        }
