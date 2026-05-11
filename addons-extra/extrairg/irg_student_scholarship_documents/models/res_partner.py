# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    irg_scholarship_type_id = fields.Many2one(
        'op.scholarship.type',
        string='Tipo de beca',
        tracking=True,
    )
    irg_scholarship_document_ids = fields.One2many(
        'irg.scholarship.document',
        'partner_id',
        string='Documentacion de beca',
    )
