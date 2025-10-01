# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Form
    is_parent = fields.Boolean(string='Is Parent')
    is_student = fields.Boolean(string='Is Student')
    studies = fields.Char(string='Studies')
    university = fields.Char(string='University')
    graduation_year = fields.Char(string='Graduation Year')

    # Moodle
    username = fields.Char(string='Username')
    birth_date = fields.Date(string='Birthday')
    institution_id = fields.Many2one(
        'res.partner', string='Institution (Dont Touch)')
    is_active = fields.Boolean(string='Active')
    is_suspended = fields.Boolean(string='Suspended')
    moodle_id = fields.Integer(string='Moodle-ID')
    gender_type = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    blood_group_type = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-')
    ])
    department_id = fields.Many2one('hr.department', string='Department')
    language_id = fields.Many2one('res.lang', string='Language')
    is_confirmed = fields.Boolean(string='Confirmed')
