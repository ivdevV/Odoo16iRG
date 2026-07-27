# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, content_disposition
import logging

_logger = logging.getLogger(__name__)


class PortalPracticeAgreement(http.Controller):

    @http.route(['/convenio/firma/<string:token>'], type='http', auth='public', website=True, sitemap=False)
    def portal_agreement_view(self, token, **kw):
        """Muestra el formulario y previsualización del convenio para firma."""
        agreement = request.env['practice.agreement'].sudo().search([('access_token', '=', token)], limit=1)
        if not agreement:
            return request.render('website.404')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        values = {
            'agreement': agreement,
            'token': token,
            'countries': countries,
            'states': states,
            'page_name': 'convenio_firma',
        }
        return request.render('irg_practice_agreement_sign.portal_agreement_page', values)

    @http.route(['/convenio/firma/<string:token>/submit'], type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def portal_agreement_submit(self, token, **post):
        """Procesa el envío del formulario y la captura de la firma digital."""
        agreement = request.env['practice.agreement'].sudo().search([('access_token', '=', token)], limit=1)
        if not agreement:
            return request.render('website.404')

        if agreement.state == 'completed':
            return request.redirect(f'/convenio/firma/{token}')

        signature_data = post.get('signature_data')
        signatory_name = post.get('signatory_name', '').strip()
        signatory_title = post.get('signatory_title', '').strip()
        center_official_name = post.get('center_official_name', '').strip()
        center_vat = post.get('center_vat', '').strip()
        street = post.get('street', '').strip()
        city = post.get('city', '').strip()
        zip_code = post.get('zip', '').strip()
        phone = post.get('phone', '').strip()

        if not signature_data:
            return request.render('irg_practice_agreement_sign.portal_agreement_page', {
                'agreement': agreement,
                'token': token,
                'error': _('Debe firmar en el recuadro antes de enviar el convenio.'),
                'countries': request.env['res.country'].sudo().search([]),
                'states': request.env['res.country.state'].sudo().search([]),
            })

        # Actualizar datos del convenio con lo introducido en el formulario
        update_vals = {}
        if center_official_name:
            update_vals['center_official_name'] = center_official_name
        if center_vat:
            update_vals['center_vat'] = center_vat
        if signatory_name:
            update_vals['signatory_name'] = signatory_name
        if signatory_title:
            update_vals['signatory_title'] = signatory_title
        if street:
            update_vals['street'] = street
        if city:
            update_vals['city'] = city
        if zip_code:
            update_vals['zip'] = zip_code
        if phone:
            update_vals['phone'] = phone

        if update_vals:
            agreement.write(update_vals)

        # Capturar la IP remota del usuario
        remote_ip = request.httprequest.headers.get('X-Forwarded-For', request.httprequest.remote_addr)
        if remote_ip and ',' in remote_ip:
            remote_ip = remote_ip.split(',')[0].strip()

        # Completar la firma y generar el PDF
        agreement.action_complete_signature(
            signature_base64=signature_data,
            signer_name=signatory_name or agreement.signatory_name,
            ip_address=remote_ip
        )

        return request.redirect(f'/convenio/firma/{token}')

    @http.route(['/convenio/descargar/<string:token>'], type='http', auth='public', website=True)
    def portal_agreement_download(self, token, **kw):
        """Descarga el PDF del convenio firmado."""
        agreement = request.env['practice.agreement'].sudo().search([('access_token', '=', token)], limit=1)
        if not agreement or not agreement.pdf_attachment_id:
            return request.render('website.404')

        attachment = agreement.pdf_attachment_id
        filecontent = attachment.raw or (attachment.datas and base64.b64decode(attachment.datas))
        if not filecontent:
            return request.render('website.404')

        filename = attachment.name or f"Convenio_{agreement.id}.pdf"
        return request.make_response(
            filecontent,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', content_disposition(filename)),
            ]
        )
