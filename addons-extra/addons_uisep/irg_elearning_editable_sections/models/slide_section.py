from odoo import api, fields, models


class IrgSlideSection(models.Model):
    _name = 'irg.slide.section'
    _description = 'Sección iRG eLearning'
    _order = 'sequence, id'

    name = fields.Char(string='Nombre', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(default=True)

    channel_id = fields.Many2one(
        'slide.channel',
        string='Curso',
        required=True,
        ondelete='cascade',
        index=True,
    )

    slide_ids = fields.One2many(
        'slide.slide',
        'irg_section_id',
        string='Contenidos',
    )

    slide_count = fields.Integer(
        string='Contenidos',
        compute='_compute_slide_count',
    )

    @api.depends('slide_ids')
    def _compute_slide_count(self):
        for section in self:
            section.slide_count = len(section.slide_ids)

    def action_open_slides(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contenidos del curso',
            'res_model': 'slide.slide',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('channel_id', '=', self.channel_id.id)],
            'context': {
                'default_channel_id': self.channel_id.id,
                'default_irg_section_id': self.id,
                'search_default_irg_section_id': self.id,
            },
        }
