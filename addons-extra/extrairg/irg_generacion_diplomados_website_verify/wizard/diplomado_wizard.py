# -*- coding: utf-8 -*-
import base64

from odoo import models, _
from odoo.exceptions import UserError


class IrgDiplomadoWizard(models.TransientModel):
    _inherit = 'irg.diplomado.wizard'

    def action_print_diplomado(self):
        self.ensure_one()
        if not self.student_id or not self.course_id:
            raise UserError(_('Debe seleccionar un estudiante y un curso válido.'))
        if not self.student_name or not self.diplomado_name:
            raise UserError(_('Debe ingresar el nombre del estudiante y del diplomado.'))

        registry = self.env['irg.diplomado.registry'].create({
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
        })

        pdf_content = self.env['report.irg_generacion_diplomados.diplomado_pdf'].generate_diplomado_pdf(
            registry._get_diplomado_pdf_data()
        )
        attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_%s.pdf' % self.student_name.replace(' ', '_'),
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'irg.diplomado.registry',
            'res_id': registry.id,
            'mimetype': 'application/pdf',
        })
        registry.write({'attachment_id': attachment.id})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
