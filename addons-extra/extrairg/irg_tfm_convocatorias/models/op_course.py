from odoo import fields, models


class OpCourse(models.Model):
    _inherit = 'op.course'

    irg_tfm_channel_id = fields.Many2one(
        'slide.channel',
        string='Canal TFM',
        ondelete='restrict',
        help='Canal eLearning asociado a los contenidos del Trabajo Final de Máster.',
    )

    def write(self, vals):
        result = super().write(vals)
        if 'irg_tfm_channel_id' not in vals:
            return result
        if not self.env.user.has_group('base.group_user'):
            return result
        theses = self.env['tesis.model'].search([
            ('course_id.course_id', 'in', self.ids),
        ])
        for thesis in theses:
            thesis._irg_reconcile_tfm_membership()
        return result
