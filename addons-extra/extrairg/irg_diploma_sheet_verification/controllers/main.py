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
        return request.env['irg.diploma.registry'].sudo().search([
            '|',
            ('verification_code', '=', code),
            ('registry_number', '=', code),
            ('state', '=', 'valid'),
        ], limit=1)

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
        code = self._normalize_code(kw.get('id') or kw.get('codigo') or kw.get('code'))
        record = self._search_odoo_registry(code)
        if record:
            return {
                'found': True,
                'code': code,
                'source': 'odoo',
                'record': record,
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
                'diploma_type': '',
                'verification_code': sheet_result.get('code'),
            })
            return sheet_result

        return {
            'found': False,
            'code': code,
            'source': 'none',
            'record': False,
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
        return request.render('irg_diploma_sheet_verification.portal_verify_diploma', result)

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
        payload = {
            'found': result['found'],
            'code': result['code'],
            'source': result['source'],
            'student_name': result['student_name'],
            'course_name': result['course_name'],
            'registry_number': result['registry_number'],
            'verification_code': result.get('verification_code') or '',
            'issue_date': str(result['issue_date']) if result['issue_date'] else '',
        }
        return request.make_json_response(payload)
