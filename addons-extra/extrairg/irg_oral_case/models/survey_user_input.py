# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError

AI_FIELDS = {'score_ia', 'resumen_ia', 'error_ai'}
ORAL_LOCK_FIELDS = {'partner_id', 'slide_id', 'survey_id', 'result_id'}


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    # Mismos nombres técnicos que dv_slide_channel_custom. Si ese módulo está
    # instalado, la columna ya existe y Odoo la reutiliza. La nota oficial no
    # vive aquí: vive en app.gradebook.result.
    score_ia = fields.Float(
        string='Nota propuesta por IA',
        help='Sugerencia de la IA. No es la nota del cuaderno y no se copia sola.',
    )
    resumen_ia = fields.Text(
        string='Resumen propuesto por IA',
        help='Comentario sugerido por la IA. No es la nota del cuaderno.',
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

    def _irg_is_oral_case(self):
        self.ensure_one()
        slide = self.sudo().slide_id
        return bool(slide and slide.oral_case_enabled)

    def _irg_slide_is_oral(self, slide_id):
        if not slide_id:
            return False
        slide = self.env['slide.slide'].sudo().browse(slide_id).exists()
        return bool(slide and slide.oral_case_enabled)

    def compute_slide_channel_partner(self):
        """El cálculo heredado no admite varias participaciones a la vez.

        Sin este bucle, guardar la nota (o cualquier flush con dos
        participaciones pendientes) lanza ValueError y deja la entrega a medias.
        La búsqueda y los campos asignados son los del módulo de origen.
        """
        for record in self:
            super(SurveyUserInput, record).compute_slide_channel_partner()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            for vals in vals_list:
                if not self._irg_slide_is_oral(vals.get('slide_id')):
                    continue
                if vals.get('result_id'):
                    raise AccessError(_(
                        'En un caso oral solo el sistema puede enlazar la libreta.'
                    ))
                partner_id = vals.get('partner_id')
                if partner_id and partner_id != self.env.user.partner_id.id:
                    raise AccessError(_(
                        'La participación del caso tiene que ser de la alumna de la sesión.'
                    ))
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if not self.env.su:
            if ORAL_LOCK_FIELDS.intersection(vals) and self.filtered(
                lambda record: record._irg_is_oral_case()
            ):
                raise AccessError(_(
                    'En un caso oral solo el sistema puede cambiar la alumna, el slide o la libreta enlazada.'
                ))
            if self._irg_slide_is_oral(vals.get('slide_id')):
                keeps_foreign_line = bool(vals.get('result_id')) or (
                    'result_id' not in vals and bool(self.filtered('result_id'))
                )
                if keeps_foreign_line:
                    raise AccessError(_(
                        'En un caso oral solo el sistema puede enlazar la libreta.'
                    ))
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
            'name': _('Confirmar nota final'),
            'res_model': 'irg.oral.case.confirm.grade',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user_input_id': self.id},
        }
