# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class OpStudent(models.Model):
    _inherit = 'op.student'

    can_generate_diplomado = fields.Boolean(
        string='Puede generar diplomado',
        compute='_compute_can_generate_diplomado',
        help=_("Verdadero si el estudiante tiene al menos un curso finalizado.")
    )

    @api.depends('course_detail_ids.state')
    def _compute_can_generate_diplomado(self):
        for student in self:
            student.can_generate_diplomado = any(course.state == 'finished' for course in student.course_detail_ids)

    def action_open_diplomado_wizard(self):
        self.ensure_one()
        return {
            'name': _('Generar Diplomado'),
            'type': 'ir.actions.act_window',
            'res_model': 'irg.diplomado.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
            }
        }
