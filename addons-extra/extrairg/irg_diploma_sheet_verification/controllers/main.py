# -*- coding: utf-8 -*-

import csv
import io
import logging
import re
from urllib.request import urlopen

from odoo import http
from odoo.addons.irg_generacion_diplomas.controllers.main import (
    IrgDiplomaVerificationController,
)
from odoo.http import request


_logger = logging.getLogger(__name__)

SHEET_CSV_URL = (
    'https://docs.google.com/spreadsheets/d/e/'
    '2PACX-1vQWMkf_KDPsymfZpgnAZwklWDraZAm2hudY9ORarnkx9dxxbNPLjcKFr_'
    '3FdKt7Z-Cvxia3hWNt2puZ/pub?output=csv'
)
HISTORICAL_CODE_PATTERN = re.compile(r'^[A-ZÁÉÍÓÚÜÑ]{3}-\d{4}$')


class IrgDiplomaSheetVerificationController(IrgDiplomaVerificationController):
    def _normalize_code(self, code):
        return (code or '').strip().replace(' ', '').upper()

    def _search_odoo_registry(self, code):
        if not code:
            return False
        record = request.env['irg.diploma.registry'].sudo().search([
            '|',
            ('verification_code', '=', code),
            ('registry_number', '=', code),
            ('state', '=', 'valid'),
        ], limit=1)
        if record:
            return record

        if 'irg.diplomado.registry' in request.env:
            diplomado = request.env['irg.diplomado.registry'].sudo().search([
                ('name', '=', code),
            ], limit=1)
            if diplomado:
                return diplomado
        return False

    def _search_sheet(self, code):
        if not code or not HISTORICAL_CODE_PATTERN.match(code):
            return False

        try:
            with urlopen(SHEET_CSV_URL, timeout=8) as response:
                content = response.read().decode('utf-8-sig')
        except Exception:
            _logger.exception('Could not fetch diploma verification Google Sheet CSV')
            return False

        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            row_code = self._normalize_code(row.get('Codigo'))
            if row_code == code:
                return {
                    'student_name': (row.get('NombreAlumno') or '').strip(),
                    'course_name': (row.get('Master') or '').strip(),
                    'code': row_code,
                    'registry_number': (row.get('registro') or '').strip(),
                    'issue_date': (row.get('fecha') or '').strip(),
                    'source': 'sheet',
                }
        return False

    def _verify_code(self, **kw):
        code, record, verified_by_stamp, record_model = super()._verify_from_registry_or_stamp(**kw)

        if not record and not verified_by_stamp and code:
            record = request.env['irg.diploma.registry'].sudo().search([
                ('verification_code', '=', code),
                ('state', '=', 'valid'),
            ], limit=1)
            if record:
                record_model = 'diploma'

        if verified_by_stamp and not record:
            student_name = ''
            course_name = ''
            issue_date = ''
            diploma_type = ''
            
            data_str = kw.get('data_str')
            stamp = kw.get('stamp')
            certificate_id = kw.get('certificate_id')
            if data_str and stamp and certificate_id and 'op.sign_certificate' in request.env:
                payload = {
                    'data_str': data_str,
                    'stamp': stamp,
                    'certificate_id': certificate_id,
                }
                verification = request.env['op.sign_certificate'].sudo().web_verify_certificate(payload)
                if verification and verification.get('Resultado de la Validación') == 'Documento Válido':
                    student_name = verification.get('student_name') or ''
                    course_name = verification.get('course_name_es') or verification.get('course_name_cat') or ''
                    issue_date = verification.get('issue_date') or ''
                    diploma_type = verification.get('diploma_type') or ''

            return {
                'found': True,
                'code': code,
                'source': 'odoo_stamp',
                'record': False,
                'record_model': 'diploma',
                'student_name': student_name,
                'course_name': course_name,
                'registry_number': code,
                'verification_code': '',
                'issue_date': issue_date,
                'diploma_type': diploma_type,
            }

        if record:
            if record_model == 'diplomado':
                return {
                    'found': True,
                    'code': code,
                    'source': 'odoo',
                    'record': record,
                    'record_model': 'diplomado',
                    'student_name': record.student_id.name if record.student_id else record.student_name or '',
                    'course_name': record.diplomado_name or (record.course_id.name if record.course_id else ''),
                    'registry_number': record.name,
                    'verification_code': '',
                    'issue_date': record.issue_date,
                    'diploma_type': dict(record._fields['diploma_type'].selection).get(
                        record.diploma_type, record.diploma_type
                    ) if 'diploma_type' in record._fields else '',
                }
            else:
                return {
                    'found': True,
                    'code': code,
                    'source': 'odoo',
                    'record': record,
                    'record_model': 'diploma',
                    'student_name': record.student_id.name if record.student_id else '',
                    'course_name': (
                        record.student_course_id.course_id.name
                        if record.student_course_id and record.student_course_id.course_id
                        else ''
                    ),
                    'registry_number': record.registry_number,
                    'verification_code': record.verification_code or '',
                    'issue_date': record.issue_date,
                    'diploma_type': dict(record._fields['diploma_type'].selection).get(
                        record.diploma_type, record.diploma_type
                    ),
                }

        sheet_result = self._search_sheet(code)
        if sheet_result:
            sheet_result.update({
                'found': True,
                'record': False,
                'record_model': 'diploma',
                'diploma_type': '',
                'verification_code': sheet_result.get('code'),
            })
            return sheet_result

        return {
            'found': False,
            'code': code,
            'source': 'none',
            'record': False,
            'record_model': False,
            'student_name': '',
            'course_name': '',
            'registry_number': '',
            'verification_code': '',
            'issue_date': '',
            'diploma_type': '',
        }

    @http.route(
        ['/verificar', '/verificar/', '/web/verificar', '/web/verificar/'],
        type='http',
        auth='public',
        website=True,
        sitemap=False,
    )
    def verify_diploma(self, **kw):
        result = self._verify_code(**kw)
        
        template = 'irg_diploma_sheet_verification.portal_verify_diploma'
        record = result.get('record')
        if record and record._name == 'irg.diplomado.registry':
            try:
                request.env.ref('irg_generacion_diplomados_website_verify.portal_verify_academic_diploma')
                template = 'irg_generacion_diplomados_website_verify.portal_verify_academic_diploma'
            except ValueError:
                pass
                
        return request.render(template, result)

    @http.route(
        ['/verificar_api', '/verificar_api/', '/web/verificar_api', '/web/verificar_api/'],
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
        sitemap=False,
    )
    def verify_diploma_api(self, **kw):
        result = self._verify_code(**kw)
        record = result.get('record')
        
        if record and record._name == 'irg.diplomado.registry':
            payload = {
                'found': True,
                'code': result['code'],
                'source': 'odoo_diplomado_registry',
                'student_name': result['student_name'],
                'course_name': result['course_name'],
                'issue_date': str(result['issue_date']) if result['issue_date'] else '',
                'document_type': 'diplomado',
            }
        else:
            payload = {
                'found': result['found'],
                'code': result['code'],
                'source': 'odoo_stamp' if result['source'] == 'odoo_stamp' else ('odoo_registry' if result['record'] else 'none'),
                'student_name': result['student_name'],
                'course_name': result['course_name'],
                'issue_date': str(result['issue_date']) if result['issue_date'] else '',
                'document_type': 'diploma' if result['record'] else '',
            }
        return request.make_json_response(payload)
