# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


class IrgOralCaseConfirmGrade(models.TransientModel):
    _name = 'irg.oral.case.confirm.grade'
    _description = 'Confirmar la nota oficial de un caso oral'

    user_input_id = fields.Many2one(
        'survey.user_input',
        string='Participación',
        required=True,
        readonly=True,
    )
    score_ia = fields.Float(
        string='Nota sugerida IA',
        related='user_input_id.score_ia',
        readonly=True,
    )
    resumen_ia = fields.Text(
        string='Resumen IA',
        related='user_input_id.resumen_ia',
        readonly=True,
    )
    error_ai = fields.Text(
        string='Error IA',
        related='user_input_id.error_ai',
        readonly=True,
    )
    official_score = fields.Float(string='Nota oficial')
    survey_type = fields.Selection(
        [
            ('exam', 'Examen'),
            ('assignment', 'Asignación'),
        ],
        string='Tipo en la libreta',
        default='exam',
        required=True,
    )
    gradebook_subject_id = fields.Many2one(
        'app.gradebook.subject',
        string='Asignatura en la libreta',
    )
    comment = fields.Text(string='Comentario del docente')
    confirm_official = fields.Boolean(
        string='Confirmo que esta nota oficial la decido yo',
    )

    def action_confirm(self):
        """Escribe la nota oficial. No copia score_ia y no usa sudo."""
        self.ensure_one()
        if not self.env.user.has_group('openeducat_core.group_op_faculty'):
            raise AccessError(_('Solo el docente puede confirmar la nota oficial.'))
        if not self.confirm_official:
            raise UserError(_(
                'Marca la confirmación. La sugerencia de la IA no se vuelca sola.'
            ))
        user_input = self.user_input_id
        slide = user_input.slide_id
        if not slide or not slide.oral_case_enabled:
            raise UserError(_('Esta participación no es un caso oral.'))
        result_model = self.env['app.gradebook.result']
        existing = result_model.search([
            ('survey_user_input_id', '=', user_input.id),
        ], limit=1)
        vals = {
            'survey_user_input_id': user_input.id,
            'scoring_total': self.official_score,
            'survey_type': self.survey_type,
            'description': _('Caso oral'),
            'comment': self.comment or False,
            'rated_by': self.env.user.partner_id.id,
            'channel_id': slide.channel_id.id,
        }
        if self.gradebook_subject_id:
            vals['gradebook_subject_id'] = self.gradebook_subject_id.id
        if existing:
            existing.write(vals)
            result = existing
        else:
            result = result_model.create(vals)
        # No se asigna user_input.result_id: isep_gradebook.write copiaría
        # scoring_percentage encima de la nota que acaba de poner el docente.
        jobs = self.env['irg.oral.case.job'].search([
            ('user_input_id', '=', user_input.id),
        ])
        if jobs:
            jobs.write({
                'gradebook_result_id': result.id,
                'official_score': self.official_score,
                'official_confirmed_by': self.env.user.id,
                'official_confirmed_at': fields.Datetime.now(),
            })
        return {'type': 'ir.actions.act_window_close'}
