# -*- coding: utf-8 -*-
from odoo import models, _


class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    def action_open_editable(self):
        """Open this subject's form in a standalone dialog, bypassing
        the One2many readonly chain from student → admission → subject."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Editar Asignatura'),
            'res_model': 'app.gradebook.subject',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'irg_op_student_admission_editable.view_gradebook_subject_editable_form'
            ).id,
            'target': 'new',
        }
