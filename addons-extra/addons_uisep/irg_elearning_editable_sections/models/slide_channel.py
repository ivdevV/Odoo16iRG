from odoo import fields, models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    irg_section_ids = fields.One2many(
        'irg.slide.section',
        'channel_id',
        string='Secciones iRG',
    )

    irg_native_section_ids = fields.One2many(
        'slide.slide',
        'channel_id',
        string='Secciones (nativas)',
        domain=[('is_category', '=', True)],
    )
