# -*- coding: utf-8 -*-
import base64
import logging
from babel.dates import format_date

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrgDiplomaGraduacionWizard(models.TransientModel):
    _name = 'irg.diploma.graduacion.wizard'
    _description = 'Asistente para Imprimir Diploma de Graduación'

    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        readonly=True
    )
    student_course_id = fields.Many2one(
        'op.student.course',
        string='Curso Académico',
        required=True,
        domain="[('student_id', '=', student_id)]"
    )
    date = fields.Date(
        string='Fecha de Expedición',
        default=fields.Date.context_today,
        required=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super(IrgDiplomaGraduacionWizard, self).default_get(fields_list)
        if 'student_id' in fields_list and not res.get('student_id'):
            res['student_id'] = self.env.context.get('active_id') or self.env.context.get('default_student_id')
        return res

    def _normalize_catalan_course_name(self, course_name):
        """Normalize common accent differences for Catalan rendering."""
        if not course_name:
            return ""
        normalized = course_name
        normalized = normalized.replace("Máster", "Màster")
        normalized = normalized.replace("máster", "màster")
        normalized = normalized.replace("Master", "Màster")
        normalized = normalized.replace("master", "màster")
        normalized = normalized.replace("Salud", "Salut")
        normalized = normalized.replace("salud", "salut")
        normalized = normalized.replace(" y ", " i ")
        normalized = normalized.replace(" Y ", " I ")
        return normalized

    def action_print_pdf(self):
        self.ensure_one()

        # Format dates using Babel
        try:
            date_es = "{} de {} de {}".format(
                self.date.day,
                format_date(self.date, format='MMMM', locale='es_ES'),
                self.date.year
            )
            date_cat = "{} de {} de {}".format(
                self.date.day,
                format_date(self.date, format='MMMM', locale='ca_ES'),
                self.date.year
            )
        except Exception as e:
            _logger.warning("Babel date format failed, falling back to simple strftime: %s", e)
            months_es = {
                1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio',
                7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
            }
            months_cat = {
                1: 'gener', 2: 'febrer', 3: 'març', 4: 'abril', 5: 'maig', 6: 'juny',
                7: 'juliol', 8: 'agost', 9: 'setembre', 10: 'octubre', 11: 'novembre', 12: 'desembre'
            }
            date_es = f"{self.date.day} de {months_es.get(self.date.month, '')} de {self.date.year}"
            date_cat = f"{self.date.day} de {months_cat.get(self.date.month, '')} de {self.date.year}"

        # Get values
        student_name = self.student_id.name or ""
        course = self.student_course_id.course_id
        course_name_es = course.name or ""
        
        course_name_cat = course.name_cat if 'name_cat' in course._fields else course_name_es
        if not course_name_cat:
            course_name_cat = course_name_es
        course_name_cat = self._normalize_catalan_course_name(course_name_cat)

        data = {
            'student_name': student_name,
            'course_name_es': course_name_es,
            'course_name_cat': course_name_cat,
            'date_es': date_es,
            'date_cat': date_cat,
        }

        # Generate PDF using ReportLab model
        report_model = self.env['report.irg_diploma_graduacion_student.diploma_pdf']
        pdf_bytes = report_model.generate_diploma_pdf(data)

        # Create attachment in Odoo
        filename = "Diploma_{}.pdf".format(
            student_name.replace(' ', '_')
        )
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_bytes),
            'res_model': 'op.student',
            'res_id': self.student_id.id,
            'mimetype': 'application/pdf',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
