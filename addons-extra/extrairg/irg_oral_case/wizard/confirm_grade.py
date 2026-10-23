# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError

from ..models.oral_case_job import validate_official_score


class IrgOralCaseConfirmGrade(models.TransientModel):
    _name = 'irg.oral.case.confirm.grade'
    _description = 'Confirmar la nota final de un caso oral'

    user_input_id = fields.Many2one(
        'survey.user_input',
        string='Participación',
        required=True,
        readonly=True,
    )
    score_ia = fields.Float(
        string='Nota propuesta por IA',
        related='user_input_id.score_ia',
        readonly=True,
        help='Sugerencia de la IA. No es la nota del cuaderno y no se copia sola.',
    )
    resumen_ia = fields.Text(
        string='Resumen propuesto por IA',
        related='user_input_id.resumen_ia',
        readonly=True,
        help='Comentario de la IA. No es la nota del cuaderno.',
    )
    error_ai = fields.Text(
        string='Error IA',
        related='user_input_id.error_ai',
        readonly=True,
    )
    official_score = fields.Float(
        string='Nota final (profesor)',
        help='Es la nota que va al cuaderno. Solo la pone el profesor. La nota de la IA no se copia sola.',
    )
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
        help='Solo si es la asignatura de esta alumna. Una asignatura sin alumna no vale.',
    )
    comment = fields.Text(string='Motivo')
    confirm_official = fields.Boolean(
        string='Confirmo que esta nota final la decido yo',
    )

    def action_confirm(self):
        """Escribe la nota final. No copia score_ia y no asigna result_id."""
        self.ensure_one()
        if not self.env.user.has_group('openeducat_core.group_op_faculty'):
            raise AccessError(_('Solo el docente puede confirmar la nota final.'))
        if not self.confirm_official:
            raise UserError(_(
                'Marca la confirmación. La sugerencia de la IA no se vuelca sola.'
            ))
        validate_official_score(self.official_score)
        subject = self.gradebook_subject_id or None
        self.env['irg.oral.case.job'].confirm_official_grade(
            self.user_input_id,
            self.official_score,
            reason=self.comment,
            survey_type=self.survey_type,
            subject=subject,
            comment=self.comment,
        )
        return {'type': 'ir.actions.act_window_close'}
