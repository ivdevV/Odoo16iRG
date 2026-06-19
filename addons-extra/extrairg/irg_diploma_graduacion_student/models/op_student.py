# -*- coding: utf-8 -*-
from odoo import models, api, _

class OpStudent(models.Model):
    _inherit = 'op.student'

    def action_open_graduation_diploma_wizard(self):
        self.ensure_one()
        return {
            'name': _('Generar Diploma de Graduación'),
            'type': 'ir.actions.act_window',
            'res_model': 'irg.diploma.graduacion.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
            }
        }
