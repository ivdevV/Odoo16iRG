# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError

AI_FIELDS = {'score_ia', 'resumen_ia', 'error_ai'}


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    # Mismos nombres técnicos que dv_slide_channel_custom. Si ese módulo está
    # instalado, la columna ya existe y Odoo la reutiliza. La nota oficial no
    # vive aquí: vive en app.gradebook.result.
    score_ia = fields.Float(
        string='Nota sugerida IA',
        help='Sugerencia de la IA. No es la nota oficial.',
    )
    resumen_ia = fields.Text(
        string='Resumen IA',
        help='Comentario sugerido por la IA. No es la nota oficial.',
    )
    error_ai = fields.Text(string='Error IA')

    def _irg_oral_case_can_write_ai_fields(self):
        user = self.env.user
        return bool(
            self.env.su
            or user.has_group('base.group_system')
            or user.has_group('openeducat_core.group_op_faculty')
            or user.has_group('irg_oral_case.group_oral_case_teacher')
        )

    def write(self, vals):
        if AI_FIELDS.intersection(vals) and not self._irg_oral_case_can_write_ai_fields():
            raise AccessError(_(
                'Solo un docente o un usuario técnico puede registrar la sugerencia de la IA.'
            ))
        return super().write(vals)

    def action_irg_oral_case_confirm_grade(self):
        """Abre el wizard. La nota se escribe solo si el docente confirma."""
        self.ensure_one()
        if not self.env.user.has_group('openeducat_core.group_op_faculty'):
            raise AccessError(_('Solo el docente puede confirmar la nota oficial.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirmar nota oficial'),
            'res_model': 'irg.oral.case.confirm.grade',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user_input_id': self.id},
        }
