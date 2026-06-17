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

    subjects_presencial = fields.Text(
        string='Asignaturas Presenciales',
        help=_("Asignaturas presenciales a incluir (separadas por línea).")
    )
    subjects_online = fields.Text(
        string='Asignaturas Online',
        help=_("Asignaturas online/virtuales a incluir (separadas por línea).")
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
            self._onchange_course_id()
        else:
            # Si no hay cursos en su ficha, dejamos los campos vacíos para que los rellene el usuario
            self.course_id = False
            self.start_date = False
            self.end_date = False

    @api.onchange('course_id')
    def _onchange_course_id(self):
        if not self.course_id:
            return

        self.diplomado_name = self.course_id.name

        # Cargar asignaturas por defecto
        self.subjects_presencial = self.course_id.irg_diplomado_subjects_presencial
        self.subjects_online = self.course_id.irg_diplomado_subjects_online

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
            'subjects_presencial': self.subjects_presencial,
            'subjects_online': self.subjects_online,
        }
        registry = self.env['irg.diplomado.registry'].create(registry_vals)

        # Formatear fechas en formato dd/mm/yyyy
        start_date_str = self.start_date.strftime('%d/%m/%Y') if self.start_date else ''
        end_date_str = self.end_date.strftime('%d/%m/%Y') if self.end_date else ''
        issue_date_str = self.issue_date.strftime('%d/%m/%Y') if self.issue_date else ''

        # Calcular la URL del QR de forma idéntica a diplomas convencionales
        from urllib.parse import urlencode
        query_params = {'id': registry.name}
        if 'op.sign_certificate' in self.env:
            stamp_payload = {
                'registry_number': registry.name,
                'student_name': self.student_name,
                'course_name_es': self.diplomado_name,
                'course_name_cat': self.diplomado_name,
                'issue_date': str(self.issue_date),
                'diploma_type': self.diploma_type,
            }
            stamp_data = self.env['op.sign_certificate'].sudo().stamp_data(stamp_payload, student=self.student_id) or {}
            if stamp_data.get('stamp') and stamp_data.get('data_str') and stamp_data.get('certificate_id'):
                query_params.update({
                    'stamp': stamp_data.get('stamp'),
                    'data_str': stamp_data.get('data_str'),
                    'certificate_id': stamp_data.get('certificate_id'),
                })

        qr_url = "https://institutoraimongaja.com/verificar/?{}".format(urlencode(query_params))

        # Construir el diccionario de datos
        data = {
            'student_name': self.student_name,
            'diplomado_name': self.diplomado_name,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'duration_hours': self.duration_hours,
            'duration_ects': self.duration_ects,
            'issue_date': issue_date_str,
            'diploma_type': self.diploma_type,
            'subjects_presencial': self.subjects_presencial or '',
            'subjects_online': self.subjects_online or '',
            'qr_url': qr_url,
            'registry_number': registry.name,
        }

        # Generar el contenido en binario mediante ReportLab
        pdf_content = self.env['report.irg_generacion_diplomados.diplomado_pdf'].generate_diplomado_pdf(data)

        # Crear un ir.attachment binario
        import base64
        attachment_name = "Diplomado_%s.pdf" % self.student_name.replace(' ', '_')
        attachment = self.env['ir.attachment'].create({
            'name': attachment_name,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'irg.diplomado.registry',
            'res_id': registry.id,
            'mimetype': 'application/pdf',
        })

        # Vincular el attachment_id en el registro del histórico
        registry.write({'attachment_id': attachment.id})

        # Retornar la acción ir.actions.act_url para descargar el PDF directamente
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
