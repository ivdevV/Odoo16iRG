from odoo import fields, models


class IrgSlideSection(models.Model):
    _inherit = 'irg.slide.section'

    convocatoria_id = fields.Many2one(
        'irg.course.convocatoria',
        string='Convocatoria',
        ondelete='set null',
        index=True,
        help='Convocatoria a la que pertenece esta sección. Opcional.',
    )
