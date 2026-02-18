# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class IrgDiplomaVerificationController(http.Controller):

    @http.route(['/verificar', '/verificar/'], type='http', auth='public', website=True, sitemap=False)
    def verify_diploma(self, **kw):
        code = (kw.get('id') or kw.get('codigo') or kw.get('code') or '').strip()
        record = False
        if code:
            record = request.env['irg.diploma.registry'].sudo().search([
                ('registry_number', '=', code),
                ('state', '=', 'valid'),
            ], limit=1)

        values = {
            'code': code,
            'record': record,
            'found': bool(record),
        }
        return request.render('irg_generacion_diplomas.portal_verify_diploma', values)