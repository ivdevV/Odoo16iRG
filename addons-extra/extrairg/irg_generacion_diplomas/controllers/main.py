# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class IrgDiplomaVerificationController(http.Controller):

    def _verify_from_registry_or_stamp(self, **kw):
        code = (kw.get('id') or kw.get('codigo') or kw.get('code') or '').strip()
        code = code.upper().replace(' ', '')
        record = False
        record_model = False
        
        if code:
            record = request.env['irg.diploma.registry'].sudo().search([
                ('registry_number', '=', code),
                ('state', '=', 'valid'),
            ], limit=1)
            if record:
                record_model = 'diploma'

        verified_by_stamp = False
        if not record:
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
                    verified_code = (verification.get('registry_number') or '').strip().upper().replace(' ', '')
                    if code and verified_code and code == verified_code:
                        verified_by_stamp = True
                    elif not code:
                        code = verified_code
                        verified_by_stamp = True

        if not record and not verified_by_stamp and code and 'irg.diplomado.registry' in request.env:
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
        
        template = 'irg_generacion_diplomas.portal_verify_diploma'
        if record_model == 'diplomado':
            try:
                request.env.ref('irg_generacion_diplomados_website_verify.portal_verify_academic_diploma')
                template = 'irg_generacion_diplomados_website_verify.portal_verify_academic_diploma'
            except ValueError:
                pass
                
        return request.render(template, values)

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