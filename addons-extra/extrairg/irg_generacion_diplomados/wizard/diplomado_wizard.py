# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
class IrgDiplomadoWizard(models.TransientModel):
    _name = 'irg.diplomado.wizard'
    _description = 'Asistente para Generación de Diplomados'

    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        help=_("Estudiante para el que se generará el diplomado.")
    )
    student_name = fields.Char(
        string='Nombre en el Diploma',
        help=_("Nombre del estudiante tal como aparecerá en el diploma.")
    )
    course_id = fields.Many2one(
        'op.course',
        string='Curso',
        help=_("Curso de referencia para la obtención de asignaturas y datos por defecto.")
    )
    diplomado_name = fields.Char(
        string='Nombre del Diplomado',
        help=_("Nombre descriptivo del diplomado que se imprimirá.")
    )
    start_date = fields.Date(
        string='Fecha de Inicio',
        help=_("Fecha de inicio de celebración.")
    )
    end_date = fields.Date(
        string='Fecha de Fin',
        help=_("Fecha de finalización de celebración.")
    )
    duration_hours = fields.Integer(
        string='Duración (Horas)',
        help=_("Duración total del diplomado en horas.")
    )
    duration_ects = fields.Float(
        string='Créditos ECTS',
        help=_("Créditos ECTS asociados al diplomado.")
    )
    issue_date = fields.Date(
        string='Fecha de Impresión',
        default=fields.Date.context_today,
        required=True,
        help=_("Fecha de expedición o impresión que figurará en el diploma.")
    )
    diploma_type = fields.Selection([
        ('digital', 'Digital'),
        ('physical', 'Físico')
    ], string='Tipo de Diploma', required=True, default='digital', help=_("Estilo del diploma a generar."))

    subject_ids = fields.Many2many(
        'op.subject',
        'irg_diplomado_wizard_subject_rel',
        'wizard_id',
        'subject_id',
        string='Asignaturas a Incluir',
        help=_("Asignaturas seleccionadas para figurar en el reverso del diplomado.")
    )

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if not self.student_id:
            return

        self.student_name = self.student_id.name

        # Buscar cursos finalizados o en curso del estudiante
        finished_courses = self.student_id.course_detail_ids.filtered(lambda c: c.state == 'finished')
        student_course = finished_courses[0] if finished_courses else (self.student_id.course_detail_ids[0] if self.student_id.course_detail_ids else False)

        if student_course:
            self.course_id = student_course.course_id.id
            if student_course.batch_id:
                self.start_date = student_course.batch_id.start_date
                self.end_date = student_course.batch_id.end_date
            return self._onchange_course_id()
        else:
            # Si no hay cursos en su ficha, dejamos los campos vacíos para que los rellene el usuario
            self.course_id = False
            self.start_date = False
            self.end_date = False
            return {'domain': {'subject_ids': [('id', '=', False)]}}

    @api.onchange('course_id')
    def _onchange_course_id(self):
        if not self.course_id:
            return {'domain': {'subject_ids': [('id', '=', False)]}}

        self.diplomado_name = self.course_id.name

        # Cargar asignaturas por defecto
        if self.course_id.irg_diplomado_subject_ids:
            self.subject_ids = [(6, 0, self.course_id.irg_diplomado_subject_ids.ids)]
        elif self.course_id.subject_ids:
            self.subject_ids = [(6, 0, self.course_id.subject_ids.ids)]
        else:
            self.subject_ids = [(5, 0, 0)]

        allowed_subjects = self.course_id.irg_diplomado_subject_ids | self.course_id.subject_ids
        return {'domain': {'subject_ids': [('id', 'in', allowed_subjects.ids)]}}
    def action_print_diplomado(self):
        self.ensure_one()
        if not self.student_id or not self.course_id:
            raise UserError(_("Debe seleccionar un estudiante y un curso válido."))
        if not self.student_name or not self.diplomado_name:
            raise UserError(_("Debe ingresar el nombre del estudiante y del diplomado."))

        # Crear el registro en el histórico
        registry_vals = {
            'student_id': self.student_id.id,
            'student_name': self.student_name,
            'course_id': self.course_id.id,
            'diplomado_name': self.diplomado_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'duration_hours': self.duration_hours,
            'duration_ects': self.duration_ects,
            'issue_date': self.issue_date,
            'diploma_type': self.diploma_type,
            'subject_ids': [(6, 0, self.subject_ids.ids)],
        }
        registry = self.env['irg.diplomado.registry'].create(registry_vals)

        # Disparar la acción de reporte QWeb para el registro creado
        report = self.env.ref('irg_generacion_diplomados.action_report_diplomado')
        return report.report_action(registry)
