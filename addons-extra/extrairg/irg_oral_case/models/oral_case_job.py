# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

DISPATCH_FIELDS = {
    'state',
    'n8n_job_id',
    'n8n_status',
    'last_error',
    'video_attachment_id',
    'video_stored_at',
    'video_purged',
}
OFFICIAL_FIELDS = {
    'gradebook_result_id',
    'official_score',
    'official_confirmed_by',
    'official_confirmed_at',
}


class IrgOralCaseJob(models.Model):
    _name = 'irg.oral.case.job'
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
        string='Copia del vídeo',
        ondelete='set null',
        copy=False,
    )
    video_stored_at = fields.Datetime(string='Vídeo guardado el', copy=False)
    video_purged = fields.Boolean(string='Vídeo borrado', default=False, copy=False)
    gradebook_result_id = fields.Many2one(
        'app.gradebook.result',
        string='Nota oficial',
        ondelete='set null',
        copy=False,
    )
    official_score = fields.Float(string='Nota oficial confirmada', copy=False)
    official_confirmed_by = fields.Many2one(
        'res.users',
        string='Confirmada por',
        ondelete='restrict',
        copy=False,
    )
    official_confirmed_at = fields.Datetime(string='Confirmada el', copy=False)
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

    _sql_constraints = [
        (
            'n8n_job_id_uniq',
            'unique(n8n_job_id)',
            'El identificador de n8n ya está registrado.',
        ),
    ]

    @api.constrains('autoevaluacion_json')
    def _check_autoevaluacion_json(self):
        for job in self:
            raw = job.autoevaluacion_json
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except (TypeError, ValueError) as exc:
                raise ValidationError(_(
                    'La autoevaluación tiene que ser un JSON válido.'
                )) from exc
            if not isinstance(parsed, (dict, list)):
                raise ValidationError(_(
                    'La autoevaluación tiene que ser un objeto o una lista JSON.'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        trusted = self.env.su or self.env.user.has_group('base.group_system')
        sanitized = []
        for vals in vals_list:
            vals = dict(vals)
            if not trusted:
                # El partner no puede venir del cliente ni de un RPC de otro usuario.
                vals['partner_id'] = self.env.user.partner_id.id
            sanitized.append(vals)
        return super().create(sanitized)

    def write(self, vals):
        vals = dict(vals)
        if self.env.context.get('irg_oral_case_dispatch'):
            extra = set(vals) - DISPATCH_FIELDS
            if extra:
                raise AccessError(_(
                    'El despacho técnico no puede modificar la nota ni el alumno.'
                ))
            return super().write(vals)
        if 'partner_id' in vals and not (
            self.env.su or self.env.user.has_group('base.group_system')
        ):
            vals.pop('partner_id')
        if OFFICIAL_FIELDS.intersection(vals) and not self.env.user.has_group(
            'openeducat_core.group_op_faculty'
        ):
            raise AccessError(_('Solo el docente puede registrar la nota oficial.'))
        return super().write(vals)

    def action_open_confirm_grade(self):
        self.ensure_one()
        if not self.env.user.has_group('openeducat_core.group_op_faculty'):
            raise AccessError(_('Solo el docente puede confirmar la nota oficial.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirmar nota oficial'),
            'res_model': 'irg.oral.case.confirm.grade',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user_input_id': self.user_input_id.id},
        }

    @api.model
    def _irg_module_operation_in_progress(self):
        # sudo: el cron consulta ir.module.module, que el usuario del cron ya
        # puede leer, y el mismo patrón vive en irg_isep_cron_update_guard.
        return bool(self.env['ir.module.module'].sudo().search_count([
            ('state', 'in', ('to install', 'to upgrade', 'to remove')),
        ]))

    @api.model
    def _cron_apply_video_retention(self):
        """Borra copias locales solo si el usuario activó la política.

        Por defecto retention_enabled está apagado y retention_days es 0.
        No borra nada hasta que se decidan los días y se active el borrado.
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
        limit_date = fields.Datetime.now() - timedelta(days=days)
        jobs = self.sudo().search([
            ('video_attachment_id', '!=', False),
            ('video_stored_at', '!=', False),
            ('video_stored_at', '<', limit_date),
            ('video_purged', '=', False),
        ])
        for job in jobs:
            attachment = job.video_attachment_id
            job.with_context(irg_oral_case_dispatch=True).sudo().write({
                'video_attachment_id': False,
                'video_purged': True,
            })
            if attachment:
                attachment.sudo().unlink()
        return True
