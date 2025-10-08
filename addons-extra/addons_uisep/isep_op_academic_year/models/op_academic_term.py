# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OpAcademicTerm(models.Model):
    _inherit = 'op.academic.term'

    code = fields.Char(string='Código del término', help='Código único para el término académico dentro del año académico.(01,02,03)') 
