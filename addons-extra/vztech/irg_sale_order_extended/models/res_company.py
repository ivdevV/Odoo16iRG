# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):

    _inherit = 'res.company'

    signature_order = fields.Binary(string='Signature Order')
