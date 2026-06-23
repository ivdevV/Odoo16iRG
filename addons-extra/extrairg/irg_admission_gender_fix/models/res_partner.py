# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Combine selection values from moodle connector and isep_openeducat_sale to avoid selection conflicts,
    # and clear the default value to avoid ValueError when creating partners without gender.
    gender = fields.Selection([
        ('m', 'Masculino'),
        ('f', 'Femenino'),
        ('o', 'Otro'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('not-sure', 'Not Sure')
    ], string='Género', default=False)

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if 'gender' in vals:
            new_gender = vals['gender']
            mapped = 'o'
            if new_gender in ('m', 'male', 'Male', 'Masculino'):
                mapped = 'm'
            elif new_gender in ('f', 'female', 'Female', 'Femenino'):
                mapped = 'f'
            
            _logger.info("IRG Gender Fix: Propagating partner gender change (%s -> %s) to admissions and students", new_gender, mapped)
            for partner in self:
                # Update admissions
                admissions = self.env['op.admission'].sudo().search([('partner_id', '=', partner.id)])
                if admissions:
                    _logger.info("IRG Gender Fix: Updating gender to '%s' for %s admissions of partner %s", mapped, len(admissions), partner.name)
                    admissions.write({'gender': mapped})
                
                # Update students
                students = self.env['op.student'].sudo().search([('partner_id', '=', partner.id)])
                if students:
                    _logger.info("IRG Gender Fix: Updating gender to '%s' for %s students of partner %s", mapped, len(students), partner.name)
                    students.write({'gender': mapped})
        return res
