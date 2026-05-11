from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrgOnlineSubjectOpening(models.Model):
    _name = 'irg.online.subject.opening'
    _description = 'IRG Online Subject Opening'
    _order = 'admission_id, sequence, subject_code, id'

    admission_id = fields.Many2one(
        'op.admission',
        string='Admision',
        required=True,
        ondelete='cascade',
        index=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Alumno',
        related='admission_id.partner_id',
        store=True,
        readonly=True,
    )
    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        related='admission_id.student_id',
        store=True,
        readonly=True,
    )
    course_id = fields.Many2one(
        'op.course',
        string='Curso',
        required=True,
        index=True,
    )
    batch_id = fields.Many2one(
        'op.batch',
        string='Lote',
        required=True,
        index=True,
    )
    subject_id = fields.Many2one(
        'op.subject',
        string='Asignatura',
        required=True,
        index=True,
    )
    subject_code = fields.Char(
        string='Codigo de asignatura',
        related='subject_id.code',
        store=True,
        readonly=True,
    )
    slide_channel_id = fields.Many2one(
        'slide.channel',
        string='Canal eLearning',
        related='subject_id.slide_channel_id',
        store=True,
        readonly=True,
    )
    sequence = fields.Integer(string='Secuencia', required=True, default=0)
    opening_date = fields.Date(string='Fecha de apertura', required=True, index=True)
    closing_date = fields.Date(string='Fecha de cierre', required=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'unique_admission_subject',
            'unique(admission_id, subject_id)',
            'Cada admision solo puede tener una apertura por asignatura.',
        ),
    ]

    @api.constrains('opening_date', 'closing_date')
    def _check_opening_dates(self):
        for record in self:
            if record.opening_date and record.closing_date and record.opening_date > record.closing_date:
                raise ValidationError(_('La fecha de apertura no puede ser posterior a la fecha de cierre.'))

    @api.constrains('admission_id', 'course_id', 'batch_id')
    def _check_admission_context(self):
        for record in self:
            if record.admission_id.course_id and record.course_id != record.admission_id.course_id:
                raise ValidationError(_('El curso debe coincidir con la admision.'))
            if record.admission_id.batch_id and record.batch_id != record.admission_id.batch_id:
                raise ValidationError(_('El lote debe coincidir con la admision.'))
