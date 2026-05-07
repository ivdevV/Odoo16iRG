from odoo import api, models, _
from odoo.exceptions import ValidationError


class OpSubjectToBatch(models.Model):
    _inherit = 'op.subject.to.batch'

    @api.onchange('subject_id')
    def _onchange_subject_id_set_code(self):
        for record in self:
            record.code = record.subject_id.code or False

    @api.model_create_multi
    def create(self, vals_list):
        subject_model = self.env['op.subject']
        for vals in vals_list:
            if vals.get('subject_id'):
                subject = subject_model.browse(vals['subject_id'])
                vals['code'] = subject.code
        return super().create(vals_list)

    def write(self, vals):
        if 'subject_id' in vals:
            if vals['subject_id']:
                subject = self.env['op.subject'].browse(vals['subject_id'])
                vals = dict(vals, code=subject.code)
            else:
                vals = dict(vals, code=False)
        return super().write(vals)

    @api.constrains('batch_id', 'subject_id')
    def _check_subject_belongs_to_batch_course(self):
        if self.env.context.get('irg_skip_subject_course_check'):
            return
        for record in self:
            if not record.batch_id or not record.subject_id:
                continue
            if record.subject_id not in record.batch_id.course_id.subject_ids:
                raise ValidationError(_(
                    'La asignatura "%(subject)s" no pertenece al curso "%(course)s" del lote.'
                ) % {
                    'subject': record.subject_id.display_name,
                    'course': record.batch_id.course_id.display_name,
                })

    @api.constrains('batch_id', 'subject_id')
    def _check_unique_subject_per_batch(self):
        for record in self:
            if not record.batch_id or not record.subject_id:
                continue
            duplicate = self.search_count([
                ('id', '!=', record.id),
                ('batch_id', '=', record.batch_id.id),
                ('subject_id', '=', record.subject_id.id),
            ])
            if duplicate:
                raise ValidationError(_(
                    'La asignatura "%(subject)s" ya esta programada en el lote "%(batch)s".'
                ) % {
                    'subject': record.subject_id.display_name,
                    'batch': record.batch_id.display_name,
                })