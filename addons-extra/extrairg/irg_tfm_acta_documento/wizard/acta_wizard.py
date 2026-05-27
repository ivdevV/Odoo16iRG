# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class IrgTfmActaWizard(models.TransientModel):
    _name = 'irg.tfm.acta.wizard'
    _description = 'Asistente de Generación de Actas de TFM/TFG'
    
    def _default_student(self):
        """Obtener el estudiante del contexto (si viene de la ficha del alumno)."""
        return self.env.context.get('active_id')
    
    # Campos principales
    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        default=_default_student,
        required=True,
        readonly=True,
        help='Estudiante para quien se genera el acta'
    )
    student_course_id = fields.Many2one(
        'op.student.course',
        string='Curso Completado',
        required=False,
        domain="[('student_id', '=', student_id)]",
        help='Curso del estudiante (opcional, para referencia)'
    )
    
    acta_type = fields.Selection(
        [
            ('tfm', 'Trabajo Final de Máster (TFM)'),
            ('tfg', 'Trabajo Final de Grado (TFG)'),
        ],
        string='Tipo de Trabajo Final',
        required=True,
        default='tfm',
        help='¿Es un TFM o TFG?'
    )
    
    # Datos académicos
    academic_year = fields.Char(
        string='Curso Académico',
        required=True,
        default=lambda self: self._default_academic_year(),
        help='Ej. 2025-2026'
    )
    degree_name = fields.Char(
        string='Titulación',
        required=True,
        help='Nombre completo (Máster Universitario en ...)'
    )
    tfm_title = fields.Text(
        string='Título del Trabajo',
        required=True,
        help='Título del TFM/TFG'
    )
    
    # Director/a
    director_name = fields.Char(
        string='Nombre del Director/a',
        required=True,
        help='Nombre del director/a'
    )
    director_surnames = fields.Char(
        string='Apellidos del Director/a',
        required=True,
        help='Apellidos del director/a'
    )
    
    # Presidente del tribunal
    president_name = fields.Char(
        string='Nombre del Presidente',
        required=True,
        help='Nombre del presidente del tribunal'
    )
    president_surnames = fields.Char(
        string='Apellidos del Presidente',
        required=True,
        help='Apellidos del presidente del tribunal'
    )
    
    # Secretario/a (quien firma)
    secretary_name = fields.Char(
        string='Nombre del Secretario/a',
        required=True,
        help='Nombre del secretario/a del tribunal'
    )
    secretary_surnames = fields.Char(
        string='Apellidos del Secretario/a',
        required=True,
        help='Apellidos del secretario/a del tribunal'
    )
    
    # Fecha de defensa
    defense_date = fields.Date(
        string='Fecha de Defensa',
        required=True,
        default=fields.Date.context_today,
        help='Fecha en que se realizó la defensa'
    )

    # Resultado
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
    
    @staticmethod
    def _default_academic_year():
        """Generar año académico por defecto (ej. 2025-2026)."""
        from datetime import datetime
        year = datetime.now().year
        return f"{year}-{year + 1}"
    
    def action_generate_acta_pdf(self):
        """Generar el PDF del acta y crear el registro."""
        self.ensure_one()
        
        # Validar que el estudiante tenga nombre y apellidos
        if not self.student_id.name:
            raise ValueError(_('El estudiante no tiene nombre registrado.'))
        
        # Preparar datos
        student_parts = self.student_id.name.split()
        student_name = student_parts[0] if student_parts else ''
        student_surnames = ' '.join(student_parts[1:]) if len(student_parts) > 1 else ''
        student_dni = getattr(self.student_id, 'id_number', '') or ''
        
        data = {
            'student_name': student_name,
            'student_surnames': student_surnames,
            'student_dni': student_dni,
            'academic_year': self.academic_year,
            'degree_name': self.degree_name,
            'tfm_title': self.tfm_title,
            'director_name': self.director_name,
            'director_surnames': self.director_surnames,
            'president_name': self.president_name,
            'president_surnames': self.president_surnames,
            'secretary_name': self.secretary_name,
            'secretary_surnames': self.secretary_surnames,
            'defense_date': str(self.defense_date),
            'acta_type': self.acta_type,
            'apto_status': self.apto_status,
        }
        
        # Generar PDF
        pdf_generator = self.env['report.irg_tfm_acta_documento.acta_pdf']
        pdf_content = pdf_generator.generate_acta_pdf(data, acta_type=self.acta_type)
        
        # Crear registro de acta sin attachment primero.
        acta = self.env['irg.tfm.acta'].create({
            'student_id': self.student_id.id,
            'student_course_id': self.student_course_id.id if self.student_course_id else None,
            'student_name': student_name,
            'student_surnames': student_surnames,
            'student_dni': student_dni,
            'academic_year': self.academic_year,
            'degree_name': self.degree_name,
            'tfm_title': self.tfm_title,
            'director_name': self.director_name,
            'director_surnames': self.director_surnames,
            'president_name': self.president_name,
            'president_surnames': self.president_surnames,
            'secretary_name': self.secretary_name,
            'secretary_surnames': self.secretary_surnames,
            'defense_date': self.defense_date,
            'acta_type': self.acta_type,
            'apto_status': self.apto_status,
            'state': 'valid',
        })

        # Crear attachment vinculado al acta.
        import base64
        type_label = 'TFM' if self.acta_type == 'tfm' else 'TFG'
        filename = f"Acta_{type_label}_{student_name}_{student_surnames}_{self.defense_date.year}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content).decode('utf-8'),
            'res_model': 'irg.tfm.acta',
            'res_id': acta.id,
            'mimetype': 'application/pdf',
        })
        acta.attachment_id = attachment
        
        # Retornar acción de descarga
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
