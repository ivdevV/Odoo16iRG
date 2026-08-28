# -*- coding: utf-8 -*-

from odoo import fields, models


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    category_id = fields.Many2one(
        'moodle.categories',
        string='Course Category',
        required=False,
    )
