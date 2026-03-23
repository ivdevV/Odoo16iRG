# -*- coding: utf-8 -*-
from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_gclid = fields.Char(string='GCLID', help='Google Click ID', index=True)
