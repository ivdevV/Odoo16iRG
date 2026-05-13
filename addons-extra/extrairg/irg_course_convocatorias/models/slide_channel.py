from odoo import fields, models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    irg_homeclass_conv_ids = fields.One2many(
        'irg.course.convocatoria',
        'channel_id',
        string='Convocatorias HomeClass',
        domain=[('modality', '=', 'homeclass')],
    )

    irg_online_conv_ids = fields.One2many(
        'irg.course.convocatoria',
        'channel_id',
        string='Convocatorias Online',
        domain=[('modality', '=', 'online')],
    )
