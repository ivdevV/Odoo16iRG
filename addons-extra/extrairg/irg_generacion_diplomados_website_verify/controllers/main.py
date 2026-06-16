# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.irg_generacion_diplomas.controllers.main import IrgDiplomaVerificationController


class IrgDiplomadoVerificationController(IrgDiplomaVerificationController):
    def _verify_from_registry_or_stamp(self, **kw):
        code, record, verified_by_stamp = super()._verify_from_registry_or_stamp(**kw)
        record_model = 'diploma' if record else False
        diplomado = False

        if not record and code:
            diplomado = request.env['irg.diplomado.registry'].sudo().search([
                ('name', '=', code),
            ], limit=1)
            if diplomado:
                record = diplomado
                record_model = 'diplomado'

        return code, record, verified_by_stamp, record_model

    @http.route(['/verificar', '/verificar/', '/web/verificar', '/web/verificar/'], type='http', auth='public', website=True, sitemap=False)
    def verify_diploma(self, **kw):
        code, record, verified_by_stamp, record_model = self._verify_from_registry_or_stamp(**kw)
        values = {
            'code': code,
            'record': record,
            'record_model': record_model,
            'found': bool(record) or verified_by_stamp,
        }
        return request.render('irg_generacion_diplomados_website_verify.portal_verify_academic_diploma', values)

    @http.route(['/verificar_api', '/verificar_api/', '/web/verificar_api', '/web/verificar_api/'], type='http', auth='public', methods=['GET'], csrf=False, sitemap=False)
    def verify_diploma_api(self, **kw):
        code, record, verified_by_stamp, record_model = self._verify_from_registry_or_stamp(**kw)
        if record_model == 'diplomado':
            payload = {
                'found': True,
                'code': code,
                'source': 'odoo_diplomado_registry',
                'student_name': record.student_id.name if record.student_id else '',
                'course_name': record.diplomado_name or (record.course_id.name if record.course_id else ''),
                'issue_date': str(record.issue_date) if record.issue_date else '',
                'document_type': 'diplomado',
            }
        else:
            payload = {
                'found': bool(record) or verified_by_stamp,
                'code': code,
                'source': 'odoo_stamp' if verified_by_stamp and not record else ('odoo_registry' if record else 'none'),
                'student_name': record.student_id.name if record and record.student_id else '',
                'course_name': record.student_course_id.course_id.name if record and record.student_course_id and record.student_course_id.course_id else '',
                'issue_date': str(record.issue_date) if record and record.issue_date else '',
                'document_type': 'diploma' if record else '',
            }
        return request.make_json_response(payload)
