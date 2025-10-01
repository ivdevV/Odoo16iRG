# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CourseAdmissionIcon(models.Model):
    _name = 'course.admission.icon'
    _description = 'CourseAdmissionIcon'

    name = fields.Char('Name')
    type = fields.Selection([
        ('admission', 'Admisión'),
        ('course', 'Curso'),
    ], string="Tipo", required=True)
    image = fields.Image("Imagen", max_width=256, max_height=256, required=True)

    _sql_constraints = [
        ('unique_type', 'unique(type)', 'Solo puede existir un ícono por tipo (Admisión o Curso).')
    ]


    @api.constrains('type')
    def _check_unique_type(self):
        for record in self:
            count = self.search_count([('type', '=', record.type)])
            if count > 1:
                raise ValidationError("Ya existe un ícono para el tipo %s" % record.type)
