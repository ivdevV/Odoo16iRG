# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OpSession(models.Model):
    _inherit = 'op.session'

    faculty_name = fields.Char('Nombre del Profesor', related='faculty_id.name')
    course_name = fields.Char('Nombre del Curso', related='course_id.name')
    subject_name = fields.Char('Nombre del Tema', related='subject_id.name')





