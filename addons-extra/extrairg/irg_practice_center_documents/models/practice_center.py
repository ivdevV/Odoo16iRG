# -*- coding: utf-8 -*-
from odoo import fields, models


class PracticeCenter(models.Model):
    _inherit = 'practice.center'

    document_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='irg_practice_center_attachment_rel',
        column1='practice_center_id',
        column2='attachment_id',
        string='Center Documents',
        copy=False,
        help='Documents associated with this practice center.',
    )
