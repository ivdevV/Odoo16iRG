# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime


class IrgTfmActa(models.Model):
    _name = 'irg.tfm.acta'
    _description = 'Acta de Evaluación de TFM/TFG'
    _order = 'created_date desc'

    name = fields.Char(
        string='Nombre del Acta',
        compute='_compute_name',
        store=True,
        help='Se genera automáticamente con formato: ALUMNO - TFM/TFG - AAAA'
    )
    
    # Relaciones
    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        ondelete='restrict',
        help='Estudiante a quien va dirigida el acta'
    )
    student_course_id = fields.Many2one(
        'op.student.course',
        string='Curso Completado',
        required=False,
        ondelete='set null',
        help='Curso del estudiante (opcional, para referencia)'
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='PDF del Acta',
        ondelete='cascade',
        help='Archivo PDF generado'
    )
    
    # Datos del estudiante (capturados en el wizard)
    student_name = fields.Char(
        string='Nombre del Estudiante',
        required=True,
        help='Nombre del alumno/a'
    )
    student_surnames = fields.Char(
        string='Apellidos del Estudiante',
        required=True,
        help='Apellidos del alumno/a'
    )
    student_dni = fields.Char(
        string='DNI del Estudiante',
        required=False,
        help='DNI o documento de identidad del alumno/a'
    )
    
    # Datos del programa y trabajo
    academic_year = fields.Char(
        string='Curso Académico',
        required=True,
        help='Ej. 2025-2026'
    )
    degree_name = fields.Char(
        string='Titulación',
        required=True,
        help='Nombre completo de la titulación (Máster Universitario en ...)'
    )
    tfm_title = fields.Text(
        string='Título del Trabajo',
        required=True,
        help='Título del TFM/TFG'
    )
    
    # Datos del tribunal
    director_name = fields.Char(
        string='Nombre del Director/a',
        required=True,
        help='Director/a del TFM/TFG'
    )
    director_surnames = fields.Char(
        string='Apellidos del Director/a',
        required=True,
        help='Apellidos del director/a del TFM/TFG'
    )
    president_name = fields.Char(
        string='Nombre del Presidente',
        required=True,
        help='Presidente del tribunal'
    )
    president_surnames = fields.Char(
        string='Apellidos del Presidente',
        required=True,
        help='Apellidos del presidente del tribunal'
    )
    secretary_name = fields.Char(
        string='Nombre del Secretario/a',
        required=True,
        help='Secretario/a del tribunal (quien firma el acta)'
    )
    secretary_surnames = fields.Char(
        string='Apellidos del Secretario/a',
        required=True,
        help='Apellidos del secretario/a del tribunal'
    )
    
    # Datos del acta (editables)
    acta_type = fields.Selection(
        [
            ('tfm', 'Trabajo Final de Máster (TFM)'),
            ('tfg', 'Trabajo Final de Grado (TFG)'),
        ],
        string='Tipo de Trabajo Final',
        required=True,
        default='tfm',
        help='Tipo de trabajo: Máster o Grado'
    )
    apto_status = fields.Selection(
        [
            ('apto', 'APTO'),
            ('no_apto', 'NO APTO'),
        ],
        string='Resultado',
        required=True,
        default='no_apto',
        help='Resultado de la evaluación: APTO o NO APTO'
    )
    defense_date = fields.Date(
        string='Fecha de Defensa',
        required=True,
        help='Fecha en que se realizó la defensa'
    )
    grade = fields.Char(
        string='Calificación',
        required=False,
        help='Calificación otorgada (ej. 8.5 / 10, Aprobado, etc.)'
    )
    observations = fields.Text(
        string='Observaciones',
        required=False,
        help='Observaciones del tribunal'
    )
    
    # Metadata
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('valid', 'Válida'),
        ],
        string='Estado',
        default='draft',
        help='Estado del acta'
    )
    created_date = fields.Datetime(
        string='Fecha de Creación',
        default=fields.Datetime.now,
        readonly=True,
        help='Fecha y hora en que se generó el acta'
    )
    created_by = fields.Many2one(
        'res.users',
        string='Creado por',
        default=lambda self: self.env.user,
        readonly=True,
        help='Usuario que generó el acta'
    )
    
    @api.depends('student_name', 'student_surnames', 'acta_type')
    def _compute_name(self):
        """Generar nombre automático del acta."""
        for record in self:
            if record.student_name and record.student_surnames and record.acta_type:
                type_label = 'TFM' if record.acta_type == 'tfm' else 'TFG'
                year = datetime.now().year
                record.name = f"{record.student_name} {record.student_surnames} - {type_label} - {year}"
            else:
                record.name = 'Acta sin título'
    
    def action_download_pdf(self):
        """Descargar el PDF del acta."""
        self.ensure_one()
        if not self.attachment_id:
            raise ValueError(_('No hay PDF generado para esta acta.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % self.attachment_id.id,
            'target': 'new',
        }
    
    def unlink(self):
        """Eliminar acta y su attachment asociado."""
        for record in self:
            if record.attachment_id:
                record.attachment_id.unlink()
        return super().unlink()
