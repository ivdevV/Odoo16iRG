# -*- coding: utf-8 -*-
from odoo import models, fields


class IrgDiplomaRegistry(models.Model):
    _name = 'irg.diploma.registry'
    _description = 'Registro de verificación de diplomas'
    _order = 'id desc'

    registry_number = fields.Char(string='Código de Registro', required=True, index=True)
    student_id = fields.Many2one('op.student', string='Estudiante', required=True)
    student_course_id = fields.Many2one('op.student.course', string='Curso del Estudiante')
    issue_date = fields.Date(string='Fecha de Expedición', required=True)
    diploma_type = fields.Selection([
        ('digital', 'Digital'),
        ('physical', 'Físico'),
    ], string='Tipo de Diploma', required=True)
    qr_url = fields.Char(string='URL QR')
    attachment_id = fields.Many2one('ir.attachment', string='Adjunto PDF')
    state = fields.Selection([
        ('valid', 'Válido'),
        ('revoked', 'Revocado'),
    ], string='Estado', default='valid', required=True)

    _sql_constraints = [
        ('unique_registry_number', 'unique(registry_number)', 'El código de registro ya existe.'),
    ]