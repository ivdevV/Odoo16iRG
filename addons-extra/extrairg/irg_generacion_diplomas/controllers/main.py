# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class IrgDiplomaVerificationController(http.Controller):

    @http.route(['/verificar', '/verificar/'], type='http', auth='public', website=True, sitemap=False)
    def verify_diploma(self, **kw):
        code = (kw.get('id') or kw.get('codigo') or kw.get('code') or '').strip()
        code = code.upper().replace(' ', '')
        record = False
        if code:
            record = request.env['irg.diploma.registry'].sudo().search([
                ('registry_number', '=', code),
                ('state', '=', 'valid'),
            ], limit=1)

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

        values = {
            'code': code,
            'record': record,
            'found': bool(record) or verified_by_stamp,
        }
        return request.render('irg_generacion_diplomas.portal_verify_diploma', values)