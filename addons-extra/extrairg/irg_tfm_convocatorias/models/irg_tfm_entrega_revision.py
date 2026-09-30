import base64

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

from .irg_tfm_logic import TfmRuleError, safe_feedback_name


_REVIEW_STATES = ('pending', 'corrections', 'approved')
_PUBLISHED_REVIEW_STATES = ('corrections', 'approved')
_RESERVED_REVIEW_CONTEXT_KEYS = frozenset({
    '_irg_tfm_private_review',
    '_irg_tfm_review_actor_id',
    'default_reviewed_by',
    'default_reviewed_at',
})


class IrgTfmEntregaRevision(models.Model):
    _name = 'irg.tfm.entrega.revision'
    _description = 'Revisión de entrega TFM'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    delivery_id = fields.Many2one(
        'irg.tfm.entrega',
        required=True,
        readonly=True,
        index=True,
        ondelete='restrict',
        tracking=True,
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo',
        related='delivery_id.attachment_id',
        readonly=True,
    )
    student_id = fields.Many2one(
        'op.student',
        string='Alumno',
        related='delivery_id.thesis_id.course_id.student_id',
        readonly=True,
    )
    version = fields.Integer(
        string='Versión',
        related='delivery_id.version',
        readonly=True,
    )
    state = fields.Selection([
        ('pending', 'Pendiente de revisión'),
        ('corrections', 'Requiere correcciones'),
        ('approved', 'Aprobada'),
    ], required=True, default='pending', tracking=True)
    comment = fields.Text(tracking=True)
    observation_file = fields.Binary(
        string='Archivo de observaciones',
        attachment=True,
    )
    observation_filename = fields.Char(string='Nombre del archivo')
    reviewed_by = fields.Many2one('res.users', readonly=True, tracking=True)
    reviewed_at = fields.Datetime(readonly=True, tracking=True)

    _sql_constraints = [(
        'irg_tfm_review_delivery_unique',
        'unique(delivery_id)',
        'Solo puede existir una revisión por versión de entrega.',
    )]

    @api.model
    def _irg_require_reviewer(self):
        if not self.env.user.has_group('irg_tfm_convocatorias.group_tfm_reviewer'):
            raise AccessError(_('Solo los revisores TFM pueden gestionar revisiones.'))
        return True

    @api.model
    def _irg_reject_public_review_controls(self, values):
        if any(field_name in values for field_name in ('reviewed_by', 'reviewed_at')):
            raise AccessError(_('Los metadatos de revisión solo puede establecerlos el servidor.'))
        if _RESERVED_REVIEW_CONTEXT_KEYS.intersection(self.env.context):
            raise AccessError(_('El contexto contiene controles de revisión reservados.'))

    @api.model
    def _irg_validate_delivery(self, delivery_id):
        try:
            delivery_id = int(delivery_id)
        except (TypeError, ValueError):
            delivery_id = 0
        delivery = self.env['irg.tfm.entrega'].browse(delivery_id).exists()
        if len(delivery) != 1:
            raise ValidationError(_('La entrega TFM seleccionada no existe.'))
        delivery.check_access_rights('read')
        delivery.check_access_rule('read')
        if delivery.stage not in ('preliminary', 'partial', 'final'):
            raise ValidationError(_('Solo se revisan entregas de convocatoria.'))
        if not delivery.thesis_id.irg_tfm_activated_at:
            raise ValidationError(_('La ficha TFM de la entrega no está activada.'))
        return delivery

    @api.model
    def _irg_validate_review_values(self, values, current=None):
        if state not in _REVIEW_STATES:
            raise ValidationError(_('El estado de revisión no es válido.'))
        if state == 'corrections' and not self._irg_review_has_feedback(values, current):
            raise ValidationError(_(
                'Indica las correcciones en el comentario o adjunta el archivo de observaciones.'
            ))
        if 'observation_file' in values or 'observation_filename' in values:
            self._irg_validate_observation(values, current)
        return state

    @api.model
    def _irg_review_has_feedback(self, values, current):
        comment = values.get('comment', current.comment if current else False)
        if (comment or '').strip():
            return True
        if 'observation_file' in values:
            return bool(values.get('observation_file'))
        return bool(current and current.observation_filename)

    @api.model
    def _irg_validate_observation(self, values, current):
        payload = values.get('observation_file', current.observation_file if current else False)
        filename = values.get(
            'observation_filename',
            current.observation_filename if current else False,
        )
        if not payload:
            return
        try:
            raw = base64.b64decode(payload)
        except (TypeError, ValueError) as exc:
            raise ValidationError(_('El archivo de observaciones no es válido.')) from exc
        try:
            safe_feedback_name(filename, len(raw))
        except TfmRuleError as exc:
            if str(exc) == 'size':
                raise ValidationError(_(
                    'El archivo de observaciones supera el límite de 20 MB.'
                )) from exc
            raise ValidationError(_(
                'Las observaciones deben ser un PDF, DOC o DOCX.'
            )) from exc

    @api.model_create_multi
    def create(self, vals_list):
        self._irg_require_reviewer()
        self.check_access_rights('create')
        for values in vals_list:
            self._irg_reject_public_review_controls(values)

        prepared_values = []
        delivery_ids = set()
        for values in vals_list:
            delivery = self._irg_validate_delivery(values.get('delivery_id'))
            if delivery.id in delivery_ids or self.search_count([('delivery_id', '=', delivery.id)]):
                raise ValidationError(_('Solo puede existir una revisión por versión de entrega.'))
            delivery_ids.add(delivery.id)
            prepared = dict(values, delivery_id=delivery.id)
            self._irg_validate_review_values(prepared)
            prepared_values.append(prepared)
        return self._irg_create_server_review(prepared_values, self.env.user)

    def _irg_create_server_review(self, vals_list, actor):
        now = fields.Datetime.now()
        server_values = []
        for values in vals_list:
            prepared = dict(values)
            if prepared.get('state', 'pending') in _PUBLISHED_REVIEW_STATES:
                prepared.update(reviewed_by=actor.id, reviewed_at=now)
            else:
                prepared.update(reviewed_by=False, reviewed_at=False)
            server_values.append(prepared)
        reviews = super().create(server_values)
        reviews._irg_invalidate_delivery_summary()
        return reviews

    def _irg_invalidate_delivery_summary(self):
        self.mapped('delivery_id').invalidate_recordset([
            'irg_tfm_review_id',
            'irg_tfm_review_state',
            'irg_tfm_reviewed_at',
        ])

    def write(self, vals):
        self._irg_require_reviewer()
        self.check_access_rights('write')
        self.check_access_rule('write')
        self._irg_reject_public_review_controls(vals)
        if 'delivery_id' in vals:
            raise AccessError(_('No se puede reasignar una revisión a otra entrega.'))

        for review in self:
            self._irg_validate_delivery(review.delivery_id.id)
            self._irg_validate_review_values(vals, current=review)
        actor = self.env.user
        for review in self:
            review._irg_write_server_review(vals, actor)
        return True

    def _irg_write_server_review(self, vals, actor):
        self.ensure_one()
        prepared = dict(vals)
        state = prepared.get('state', self.state)
        if state in _PUBLISHED_REVIEW_STATES:
            prepared.update(
                reviewed_by=actor.id,
                reviewed_at=fields.Datetime.now(),
            )
        else:
            prepared.update(reviewed_by=False, reviewed_at=False)
        result = super().write(prepared)
        self._irg_invalidate_delivery_summary()
        return result

    def unlink(self):
        raise AccessError(_('Las revisiones de entregas TFM no se pueden eliminar.'))
