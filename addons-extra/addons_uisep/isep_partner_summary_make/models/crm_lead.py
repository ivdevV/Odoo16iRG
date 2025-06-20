# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    summary_ids=fields.One2many(
        'res.call.summary',
        'crm_lead_id',string="Resúmen de llamadas")


