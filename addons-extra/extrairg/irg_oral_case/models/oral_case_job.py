# -*- coding: utf-8 -*-
import math

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.mail import plaintext2html
from markupsafe import Markup

SYSTEM_FIELDS = {
    'partner_id',
    'slide_id',
    'survey_id',
    'user_input_id',
    'case_code',
    'consent_date',
    'duration_seconds',
    'autoevaluacion_json',
    'state',
    'n8n_job_id',
    'n8n_status',
    'last_error',
    'video_attachment_id',
    'video_stored_at',
    'video_purged',
    'gradebook_result_id',
    'official_confirmed_by',
    'official_confirmed_at',
}
FACULTY_FIELDS = {
    'official_score',
    'official_score_reason',
}


def validate_official_score(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValidationError(_('La nota final tiene que ser un número del 0 al 10.'))
    if value < 0 or value > 10:
        raise ValidationError(_('La nota final tiene que estar entre 0 y 10.'))


def attachment_is_case_video(attachment, res_model, res_id):
    return bool(
        attachment
        and attachment.exists()
        and attachment.res_model == res_model
        and attachment.res_id == res_id
        and attachment.mimetype == 'video/webm'
        and not attachment.public
    )


class IrgOralCaseJob(models.Model):
    _name = 'irg.oral.case.job'
    _inherit = ['mail.thread']
    _description = 'Entrega de caso oral'
    _order = 'id desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Alumno',
        required=True,
        index=True,
        ondelete='restrict',
    )
    slide_id = fields.Many2one(
        'slide.slide',
        string='Slide',
        required=True,
        ondelete='restrict',
        index=True,
    )
    survey_id = fields.Many2one('survey.survey', string='Encuesta', ondelete='restrict')
    user_input_id = fields.Many2one(
        'survey.user_input',
        string='Participación',
        ondelete='restrict',
        index=True,
    )
    case_code = fields.Char(string='Código del caso', required=True)
    consent_date = fields.Datetime(string='Fecha de consentimiento', required=True)
    duration_seconds = fields.Float(string='Duración (segundos)')
    autoevaluacion_json = fields.Text(string='Autoevaluación')
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('accepted', 'Aceptado por n8n'),
            ('rejected', 'Rechazado por n8n'),
            ('error', 'Error de envío'),
        ],
        string='Estado',
        default='draft',
        required=True,
    )
    n8n_job_id = fields.Char(string='Job n8n', index=True, copy=False)
    n8n_status = fields.Char(string='Estado n8n')
    last_error = fields.Text(string='Último error')
    video_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Grabación',
        ondelete='set null',
        copy=False,
    )
    video_stored_at = fields.Datetime(string='Vídeo guardado el', copy=False)
    video_purged = fields.Boolean(string='Vídeo borrado', default=False, copy=False)
    gradebook_result_id = fields.Many2one(
        'app.gradebook.result',
        string='Línea del cuaderno',
        ondelete='set null',
        copy=False,
    )
    official_score = fields.Float(
        string='Nota final (profesor)',
        copy=False,
        help='Es la nota que va al cuaderno. Solo la pone el profesor. La nota de la IA no se copia sola.',
    )
    official_score_reason = fields.Char(
        string='Motivo del cambio',
        help='Opcional. Queda en el historial junto con quién cambió la nota y cuándo.',
    )
    official_confirmed_by = fields.Many2one(
        'res.users',
        string='Nota final puesta por',
        ondelete='restrict',
        copy=False,
    )
    official_confirmed_at = fields.Datetime(string='Nota final puesta el', copy=False)
    score_ia = fields.Float(
        string='Nota propuesta por IA',
        related='user_input_id.score_ia',
        readonly=True,
        help='Sugerencia de la IA para el caso. No es la nota del cuaderno y no se copia sola.',
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
    clip_ids = fields.One2many(
        'irg.oral.case.clip',
        'job_id',
        string='Intervenciones',
    )
    video_kept = fields.Boolean(
        string='Vídeo guardado',
        compute='_compute_video_review',
        help='Indica si esta entrega tiene grabación conservada en Odoo. No activa ni desactiva la copia.',
    )
    video_policy_keeps = fields.Boolean(
        string='El caso conserva vídeos',
        compute='_compute_video_review',
    )
    video_review_html = fields.Html(
        string='Grabaciones',
        compute='_compute_video_review',
        sanitize=False,
    )

    _sql_constraints = [
        (
            'n8n_job_id_uniq',
            'unique(n8n_job_id)',
            'El identificador de n8n ya está registrado.',
        ),
    ]

    @api.depends(
        'video_attachment_id',
        'clip_ids.video_attachment_id',
        'slide_id',
        'slide_id.oral_case_keep_video',
    )
    def _compute_video_review(self):
        global_keep = str(self.env['ir.config_parameter'].sudo().get_param(
            'irg_oral_case.store_video_copy', 'False',
        ) or '').strip().lower() in ('1', 'true', 'yes', 'on')
        for job in self:
            slide = job.sudo().slide_id
            job.video_policy_keeps = bool(
                (slide and slide.oral_case_keep_video) or global_keep
            )
            parts = []
            if attachment_is_case_video(job.video_attachment_id, 'irg.oral.case.job', job.id):
                parts.append(
                    '<video controls preload="metadata" src="/irg/oral_case/media/job/%d" '
                    'style="max-width:100%%"></video>' % job.id
                )
            for clip in job.clip_ids.sorted(key=lambda item: (item.segment_index, item.id)):
                if attachment_is_case_video(
                    clip.video_attachment_id, 'irg.oral.case.clip', clip.id,
                ):
                    parts.append(
                        '<video controls preload="metadata" '
                        'src="/irg/oral_case/media/job/%d/clip/%d" style="max-width:100%%"></video>'
                        % (job.id, clip.id)
                    )
            job.video_kept = bool(parts)
            job.video_review_html = Markup(''.join(parts)) if parts else False

    @api.constrains('autoevaluacion_json')
    def _check_autoevaluacion_json(self):
        for job in self:
            raw = job.autoevaluacion_json
            if not raw:
                continue
            parsed = self._json_value(raw)
            if parsed is None:
                raise ValidationError(_(
                    'La autoevaluación tiene que ser un objeto o una lista JSON.'
                ))

    @api.constrains('official_score')
    def _check_official_score_range(self):
        for job in self:
            validate_official_score(job.official_score or 0.0)

    @staticmethod
    def _json_value(raw):
        import json
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return None
        if not isinstance(parsed, (dict, list)):
            return None
        return parsed

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise AccessError(_('Solo el sistema puede crear la entrega.'))
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if self.env.su:
            return super().write(vals)
        if set(vals) - FACULTY_FIELDS or not self.env.user.has_group(
            'openeducat_core.group_op_faculty'
        ):
            raise AccessError(_('Solo el profesor puede cambiar la nota final.'))
        previous = {}
        if 'official_score' in vals:
            validate_official_score(vals['official_score'])
            previous = {
                job.id: (job.official_score, bool(job.official_confirmed_at))
                for job in self
            }
        result = super().write(vals)
        if 'official_score' in vals:
            reason = vals.get('official_score_reason')
            for job in self:
                old_score, was_confirmed = previous[job.id]
                job.confirm_official_grade(
                    job.user_input_id,
                    vals['official_score'],
                    reason=reason if reason is not None else job.official_score_reason,
                    previous_score=old_score if was_confirmed else None,
                )
        return result

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('Solo el sistema puede borrar la entrega.'))
        return super().unlink()

    @api.model
    def confirm_official_grade(self, user_input, score, reason=None, survey_type='exam',
                               subject=None, comment=None, previous_score='unset'):
        """Crea o actualiza la línea del cuaderno de esta participación.

        La libreta se escribe con el usuario docente. El enlace del job lo
        escribe el superusuario con un diccionario fijo. El uid del docente
        se captura antes de ese sudo.
        """
        validate_official_score(score)
        teacher = self.env.user
        if not teacher.has_group('openeducat_core.group_op_faculty'):
            raise AccessError(_('Solo el docente puede confirmar la nota final.'))
        if not user_input:
            raise UserError(_('Esta entrega no tiene participación.'))
        slide = user_input.sudo().slide_id
        if not slide or not slide.oral_case_enabled:
            raise UserError(_('Esta participación no es un caso oral.'))
        student = user_input.sudo().partner_id
        jobs = self.sudo().search([('user_input_id', '=', user_input.id)])
        for job in jobs:
            if job.partner_id != student or job.slide_id != slide:
                raise AccessError(_('La entrega no corresponde a esta alumna y a este caso.'))
        if subject:
            subject_partner = subject.sudo().partner_id
            if not subject_partner or subject_partner != student:
                raise AccessError(_('La asignatura no es de esta alumna.'))
        if previous_score == 'unset':
            confirmed = jobs.filtered('official_confirmed_at')[:1]
            previous_score = confirmed.official_score if confirmed else None
        result = self._gradebook_line(jobs, user_input, student, slide)
        teacher_partner_id = teacher.partner_id.id
        teacher_id = teacher.id
        if result:
            # jobs.sudo() deja el Many2one en superusuario. La nota la escribe
            # el docente: si no, el write se salta las reglas de la libreta.
            result = self.env['app.gradebook.result'].browse(result.id)
            self._assert_gradebook_line(result, user_input, student, slide)
            result.write({
                'scoring_total': score,
                'rated_by': teacher_partner_id,
            })
            if comment:
                result.write({'comment': comment})
        else:
            vals = {
                'survey_user_input_id': user_input.id,
                'scoring_total': score,
                'survey_type': survey_type or 'exam',
                'description': _('Caso oral'),
                'rated_by': teacher_partner_id,
                'channel_id': slide.channel_id.id,
            }
            if comment:
                vals['comment'] = comment
            enrollment = self.env['slide.channel.partner'].sudo().search([
                ('channel_id', '=', slide.channel_id.id),
                ('partner_id', '=', student.id),
            ], limit=1)
            if enrollment:
                vals['channel_partner_id'] = enrollment.id
            if subject:
                vals['gradebook_subject_id'] = subject.id
            result = self.env['app.gradebook.result'].create(vals)
        if jobs:
            link_vals = {
                'gradebook_result_id': result.id,
                'official_score': score,
                'official_confirmed_by': teacher_id,
                'official_confirmed_at': fields.Datetime.now(),
            }
            if reason:
                link_vals['official_score_reason'] = reason
            jobs.sudo().write(link_vals)
            old_label = _('sin nota') if previous_score is None else ('%.1f' % previous_score)
            text = _(
                'Nota final (profesor): %(old)s → %(new)s. La cambió %(user)s. Motivo: %(reason)s'
            ) % {
                'old': old_label,
                'new': '%.1f' % score,
                'user': teacher.name,
                'reason': reason or _('sin motivo'),
            }
            for job in jobs:
                job.sudo().message_post(
                    body=plaintext2html(text),
                    author_id=teacher_partner_id,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )
        return result

    def _gradebook_line(self, jobs, user_input, student, slide):
        linked = jobs.mapped('gradebook_result_id')
        if len(linked) > 1 and len(set(linked.ids)) > 1:
            raise AccessError(_('La entrega tiene más de una línea de cuaderno.'))
        result = linked[:1]
        if result and result.survey_user_input_id != user_input:
            raise AccessError(_('La línea del cuaderno no es de esta participación.'))
        if not result:
            result = self.env['app.gradebook.result'].search([
                ('survey_user_input_id', '=', user_input.id),
            ], limit=1)
        if result:
            self._assert_gradebook_line(result, user_input, student, slide)
        return result

    def _assert_gradebook_line(self, result, user_input, student, slide):
        # La lectura del vínculo es de integridad. La escritura de la nota
        # sigue en el entorno de quien llama.
        checked = result.sudo()
        if checked.survey_user_input_id != user_input:
            raise AccessError(_('La línea del cuaderno no es de esta participación.'))
        subject = checked.gradebook_subject_id
        if subject:
            subject_partner = subject.partner_id
            if not subject_partner or subject_partner != student:
                raise AccessError(_('La línea del cuaderno no es de esta alumna.'))
            return
        enrollment = checked.channel_partner_id
        if enrollment and enrollment.partner_id != student:
            raise AccessError(_('La línea del cuaderno no es de esta alumna.'))
        if enrollment and enrollment.channel_id != slide.channel_id:
            raise AccessError(_('La línea del cuaderno no es de este caso.'))

    def action_open_confirm_grade(self):
        self.ensure_one()
        if not self.env.user.has_group('openeducat_core.group_op_faculty'):
            raise AccessError(_('Solo el docente puede confirmar la nota final.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirmar nota final'),
            'res_model': 'irg.oral.case.confirm.grade',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user_input_id': self.user_input_id.id},
        }

    @api.model
    def _irg_module_operation_in_progress(self):
        return bool(self.env['ir.module.module'].sudo().search_count([
            ('state', 'in', ('to install', 'to upgrade', 'to remove')),
        ]))

    @api.model
    def _cron_apply_video_retention(self):
        """Borra copias locales solo si el usuario activó la política.

        Un puntero que no es el webm de esta entrega se limpia y el fichero
        ajeno se queda.
        """
        if self._irg_module_operation_in_progress():
            return False
        params = self.env['ir.config_parameter'].sudo()
        enabled = str(params.get_param('irg_oral_case.retention_enabled', 'False') or '')
        if enabled.strip().lower() not in ('1', 'true', 'yes', 'on'):
            return False
        try:
            days = int(params.get_param('irg_oral_case.retention_days', '0') or 0)
        except (TypeError, ValueError):
            days = 0
        if days <= 0:
            return False
        from datetime import timedelta
        limit_date = fields.Datetime.now() - timedelta(days=days)
        jobs = self.sudo().search([
            ('video_stored_at', '!=', False),
            ('video_stored_at', '<', limit_date),
            ('video_purged', '=', False),
        ])
        for job in jobs:
            self._purge_case_attachment(job.video_attachment_id, 'irg.oral.case.job', job.id)
            for clip in job.clip_ids:
                self._purge_case_attachment(
                    clip.video_attachment_id, 'irg.oral.case.clip', clip.id,
                )
                if clip.video_attachment_id:
                    clip.sudo().write({'video_attachment_id': False})
            job.sudo().write({
                'video_attachment_id': False,
                'video_purged': True,
            })
        return True

    @api.model
    def _purge_case_attachment(self, attachment, res_model, res_id):
        if not attachment:
            return
        if attachment_is_case_video(attachment, res_model, res_id):
            attachment.sudo().unlink()
