from odoo import fields, models


class OpBatch(models.Model):
    _inherit = 'op.batch'

    irg_course_subject_ids = fields.Many2many(
        comodel_name='op.subject',
        related='course_id.subject_ids',
        string='Course Subjects',
        readonly=True,
    )

    def write(self, vals):
        if 'course_id' in vals:
            batch_records = self.with_context(irg_skip_subject_course_check=True)
            return super(OpBatch, batch_records).write(vals)
        return super().write(vals)