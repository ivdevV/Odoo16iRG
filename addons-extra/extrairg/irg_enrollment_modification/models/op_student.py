# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.exceptions import AccessError


class OpStudent(models.Model):
    _inherit = 'op.student'

    def action_open_enrollment_change_wizard(self):
        self.ensure_one()
        if not self.env['irg.enrollment.change']._is_academic_user():
            raise AccessError(
                _('No tiene permisos para solicitar una modificación de matrícula.')
            )
        return {
            'name': _('Modificación de matrícula'),
            'type': 'ir.actions.act_window',
            'res_model': 'irg.enrollment.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
            },
        }
