# -*- coding: utf-8 -*-

import base64
import unicodedata
from urllib.parse import urlencode

from babel.dates import format_date

from odoo import models


VERIFY_BASE_URL = 'https://app.institutoraimongaja.com/verificar/'


class DiplomaWizard(models.TransientModel):
    _inherit = 'irg.diploma.wizard'

    def _get_student_verification_prefix(self):
        self.ensure_one()
        normalized = unicodedata.normalize('NFKD', self.student_id.name or '')
        ascii_name = ''.join(char for char in normalized if not unicodedata.combining(char))
        letters = ''.join(char for char in ascii_name.upper() if char.isalpha())
        return (letters[:3] or 'IRG').ljust(3, 'X')

    def _next_verification_code(self):
        self.ensure_one()
        prefix = self._get_student_verification_prefix()
        sequence = self.env['ir.sequence'].next_by_code('irg.diploma.verification.code') or '0000'
        return '{}-{}'.format(prefix, sequence)

    def action_print_diploma(self):
        self.ensure_one()

        registry_number = self.env['ir.sequence'].next_by_code('irg.diploma.registry') or 'DRAFT'
        verification_code = self._next_verification_code()

        date_es = '{} de {} de {}'.format(
            self.date.day,
            format_date(self.date, format='MMMM', locale='es_ES'),
            self.date.year,
        )
        date_cat = '{} de {} de {}'.format(
            self.date.day,
            format_date(self.date, format='MMMM', locale='ca_ES'),
            self.date.year,
        )

        student_name = self.student_id.name or ''
        course_name_es = self.student_course_id.course_id.name
        course_name_cat = getattr(self.student_course_id.course_id, 'name_cat', None) or course_name_es
        normer = self.env['report.irg_generacion_diplomas.diploma_pdf']
        course_name_cat = normer._normalize_catalan_course_name(course_name_cat)

        query_params = {'id': verification_code}
        if 'op.sign_certificate' in self.env:
            stamp_payload = {
                'registry_number': registry_number,
                'verification_code': verification_code,
                'student_name': student_name,
                'course_name_es': course_name_es,
                'course_name_cat': course_name_cat,
                'issue_date': str(self.date),
                'diploma_type': self.diploma_type,
            }
            stamp_data = self.env['op.sign_certificate'].sudo().stamp_data(
                stamp_payload, student=self.student_id
            ) or {}
            if stamp_data.get('stamp') and stamp_data.get('data_str') and stamp_data.get('certificate_id'):
                query_params.update({
                    'stamp': stamp_data.get('stamp'),
                    'data_str': stamp_data.get('data_str'),
                    'certificate_id': stamp_data.get('certificate_id'),
                })

        qr_url = '{}?{}'.format(VERIFY_BASE_URL, urlencode(query_params))

        def html_split(name, lang='es'):
            if not name:
                return name
            sep = ' y ' if lang == 'es' else ' i '
            if sep in name:
                parts = name.rsplit(sep, 1)
                return parts[0] + sep.strip() + '<br/>' + parts[1]
            return name

        data = {
            'student_name': student_name,
            'course_name_es': course_name_es,
            'course_name_cat': course_name_cat,
            'course_name_es_html': html_split(course_name_es, lang='es'),
            'course_name_cat_html': html_split(course_name_cat, lang='cat'),
            'date_es': date_es,
            'date_cat': date_cat,
            'registry_number': registry_number,
            'verification_code': verification_code,
            'qr_url': qr_url,
        }

        pdf_generator = self.env['report.irg_generacion_diplomas.diploma_pdf']
        pdf_content = pdf_generator.generate_diploma_pdf(data, diploma_type=self.diploma_type)

        filename = 'Diploma_{}_{}.pdf'.format(
            student_name.replace(' ', '_'),
            self.diploma_type.capitalize(),
        )

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'op.student',
            'res_id': self.student_id.id,
            'mimetype': 'application/pdf',
        })

        self.env['irg.diploma.registry'].sudo().create({
            'registry_number': registry_number,
            'verification_code': verification_code,
            'student_id': self.student_id.id,
            'student_course_id': self.student_course_id.id,
            'issue_date': self.date,
            'diploma_type': self.diploma_type,
            'qr_url': qr_url,
            'attachment_id': attachment.id,
            'state': 'valid',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
