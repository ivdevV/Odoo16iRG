from odoo import fields, models


class OpCourse(models.Model):
    _inherit = 'op.course'

    irg_modality_ids = fields.Many2many(
        'irg.course.modality',
        'op_course_irg_modality_rel',
        'course_id',
        'modality_id',
        string='Modalidades',
        help=(
            'Modalidades de impartición disponibles para este curso. '
            'La modalidad Online aplica a los lotes con código ONL (excepto MONL).'
        ),
    )
