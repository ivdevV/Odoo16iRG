import base64

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

from .irg_tfm_logic import (
    TfmRuleError,
    safe_feedback_name,
)


class IrgTfmVentanaAlumno(models.Model):
    _name = 'irg.tfm.ventana.alumno'
    _description = 'Ventana de entrega TFM por alumno'
    _order = 'thesis_id, stage'

    thesis_id = fields.Many2one(
        'tesis.model', required=True, ondelete='cascade', index=True,
    )
    stage = fields.Selection(
        [
            ('preliminary', 'Observaciones previas a la entrega'),
            ('partial', 'Entrega parcial'),
            ('final', 'Entrega final'),
        ],
        required=True,
    )
    open_date = fields.Date(string='Apertura')
    close_date = fields.Date(string='Cierre')

    _sql_constraints = [(
        'irg_tfm_ventana_alumno_unique',
        'unique(thesis_id, stage)',
        'Ya existe una ventana para esta etapa del alumno.',
    )]

    def _irg_require_internal(self):
        if not self.env.user.has_group('base.group_user'):
            raise AccessError(_('Solo un usuario interno puede cambiar la ventana de un alumno.'))

    @api.constrains('open_date', 'close_date')
    def _check_window(self):
        for record in self:
            if not record.open_date and not record.close_date:
                raise ValidationError(_(
                    'Indica la apertura, el cierre, o las dos fechas de la ventana del alumno.'
                ))
            if record.open_date and record.close_date and record.open_date > record.close_date:
                raise ValidationError(_(
                    'La apertura del alumno no puede ser posterior al cierre.'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        self._irg_require_internal()
        return super().create(vals_list)

    def write(self, vals):
        self._irg_require_internal()
        return super().write(vals)

    def unlink(self):
        self._irg_require_internal()
        return super().unlink()


class IrgTfmEsquemaFeedback(models.Model):
    _name = 'irg.tfm.esquema.feedback'
    _description = 'Retroalimentación del esquema TFM'

    outline_id = fields.Many2one(
        'irg.tfm.esquema', required=True, ondelete='cascade', index=True,
    )
    file = fields.Binary(attachment=True, required=True)
    filename = fields.Char(required=True)
    uploaded_by = fields.Many2one('res.users', readonly=True)
    uploaded_at = fields.Datetime(readonly=True)

    _sql_constraints = [(
        'irg_tfm_esquema_feedback_unique',
        'unique(outline_id)',
        'Solo puede haber un archivo de retroalimentación por versión del esquema.',
    )]

    def _irg_require_reviewer(self):
        if not self.env.user.has_group('irg_tfm_convocatorias.group_tfm_reviewer'):
            raise AccessError(_('Solo un revisor TFM puede subir la retroalimentación del esquema.'))

    @api.model
    def _irg_prepare_file(self, values):
        filename = values.get('filename')
        payload = values.get('file')
        if not payload:
            raise ValidationError(_('Adjunta el archivo de retroalimentación.'))
        try:
            raw = base64.b64decode(payload)
        except (TypeError, ValueError) as exc:
            raise ValidationError(_('El archivo de retroalimentación no es válido.')) from exc
        try:
            safe_name = safe_feedback_name(filename, len(raw))
        except TfmRuleError as exc:
            if str(exc) == 'size':
                raise ValidationError(_(
                    'El archivo de retroalimentación supera el límite de 20 MB.'
                )) from exc
            raise ValidationError(_(
                'La retroalimentación debe ser un PDF, DOC o DOCX.'
            )) from exc
        return {
            'file': payload,
            'filename': safe_name,
            'uploaded_by': self.env.user.id,
            'uploaded_at': fields.Datetime.now(),
        }

    @api.model
    def _irg_store(self, outline, values):
        self._irg_require_reviewer()
        if outline.state != 'done':
            raise ValidationError(_('Solo se retroalimenta un esquema ya enviado.'))
        prepared = self._irg_prepare_file(values)
        prepared['outline_id'] = outline.id
        existing = self.sudo().search([('outline_id', '=', outline.id)], limit=1)
        if existing:
            super(IrgTfmEsquemaFeedback, existing).write(prepared)
            return existing
        return super().create([prepared])

    @api.model_create_multi
    def create(self, vals_list):
        self._irg_require_reviewer()
        prepared = []
        for values in vals_list:
            if values.get('uploaded_by') or values.get('uploaded_at'):
                raise AccessError(_('La autoría de la retroalimentación la fija el servidor.'))
            outline = self.env['irg.tfm.esquema'].browse(values.get('outline_id')).exists()
            if len(outline) != 1 or outline.state != 'done':
                raise ValidationError(_('Solo se retroalimenta un esquema ya enviado.'))
            row = self._irg_prepare_file(values)
            row['outline_id'] = outline.id
            prepared.append(row)
        return super().create(prepared)

    def write(self, vals):
        self._irg_require_reviewer()
        if 'outline_id' in vals:
            raise AccessError(_('No se puede mover la retroalimentación a otro esquema.'))
        if 'uploaded_by' in vals or 'uploaded_at' in vals:
            raise AccessError(_('La autoría de la retroalimentación la fija el servidor.'))
        if 'file' in vals or 'filename' in vals:
            for record in self:
                merged = {
                    'file': vals.get('file', record.file),
                    'filename': vals.get('filename', record.filename),
                }
                prepared = self._irg_prepare_file(merged)
                super(IrgTfmEsquemaFeedback, record).write(prepared)
            return True
        return super().write(vals)

    def unlink(self):
        raise AccessError(_('La retroalimentación del esquema no se elimina.'))


class IrgTfmEsquemaFeedbackWizard(models.TransientModel):
    _name = 'irg.tfm.esquema.feedback.wizard'
    _description = 'Subir retroalimentación del esquema TFM'

    outline_id = fields.Many2one('irg.tfm.esquema', required=True)
    file = fields.Binary(required=True)
    filename = fields.Char(required=True)

    def action_apply(self):
        self.ensure_one()
        self.env['irg.tfm.esquema.feedback']._irg_store(self.outline_id, {
            'file': self.file,
            'filename': self.filename,
        })
        return {'type': 'ir.actions.act_window_close'}
