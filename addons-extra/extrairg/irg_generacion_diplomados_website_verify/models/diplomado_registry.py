# -*- coding: utf-8 -*-
import base64
from urllib.parse import urlencode

from odoo import models


class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'

    def _get_diplomado_verification_base_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        return base_url.rstrip('/')

    def _build_diplomado_verification_qr_url(self):
        self.ensure_one()
        query_params = {'id': self.name}
        if 'op.sign_certificate' in self.env:
            stamp_payload = {
                'registry_number': self.name,
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

        return '%s/verificar/?%s' % (
            self._get_diplomado_verification_base_url(),
            urlencode(query_params),
        )

    def _get_diplomado_pdf_data(self):
        self.ensure_one()
        return {
            'student_name': self.student_name,
            'diplomado_name': self.diplomado_name,
            'start_date': self.start_date.strftime('%d/%m/%Y') if self.start_date else '',
            'end_date': self.end_date.strftime('%d/%m/%Y') if self.end_date else '',
            'duration_hours': self.duration_hours,
            'duration_ects': self.duration_ects,
            'issue_date': self.issue_date.strftime('%d/%m/%Y') if self.issue_date else '',
            'diploma_type': self.diploma_type,
            'subjects_presencial': self.subjects_presencial or '',
            'subjects_online': self.subjects_online or '',
            'qr_url': self._build_diplomado_verification_qr_url(),
            'registry_number': self.name,
        }

    def action_reprint(self):
        self.ensure_one()
        if not self.attachment_id:
            pdf_content = self.env['report.irg_generacion_diplomados.diplomado_pdf'].generate_diplomado_pdf(
                self._get_diplomado_pdf_data()
            )
            attachment = self.env['ir.attachment'].create({
                'name': 'Diplomado_%s.pdf' % self.student_name.replace(' ', '_'),
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'irg.diplomado.registry',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            self.write({'attachment_id': attachment.id})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % self.attachment_id.id,
            'target': 'self',
        }
