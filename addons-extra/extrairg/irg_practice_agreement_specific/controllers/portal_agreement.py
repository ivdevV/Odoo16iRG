# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.addons.irg_practice_agreement_sign.controllers.portal_agreement import (
    PortalPracticeAgreement,
)
from odoo.http import request, content_disposition
import base64


class PortalPracticeAgreementSpecific(PortalPracticeAgreement):

    def _find_agreement_by_center_token(self, token):
        return request.env['practice.agreement'].sudo().search(
            [('access_token', '=', token)], limit=1
        )

    def _find_agreement_by_student_token(self, token):
        return request.env['practice.agreement'].sudo().search(
            [('student_access_token', '=', token)], limit=1
        )

    @http.route(
        ['/convenio/firma/<string:token>'],
        type='http',
        auth='public',
        website=True,
        sitemap=False,
    )
    def portal_agreement_view(self, token, **kw):
        agreement = self._find_agreement_by_center_token(token)
        if (
            agreement
            and agreement._is_especifico()
            and agreement.signature_center
            and not agreement.signature_student
            and agreement.state != 'completed'
        ):
            return request.render(
                'irg_practice_agreement_specific.portal_agreement_waiting_student',
                {
                    'agreement': agreement,
                    'token': token,
                    'page_name': 'convenio_firma',
                },
            )
        return super().portal_agreement_view(token, **kw)

    @http.route(
        ['/convenio/firma/<string:token>/submit'],
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def portal_agreement_submit(self, token, **post):
        agreement = self._find_agreement_by_center_token(token)
        if agreement and agreement._is_especifico() and agreement.signature_center:
            return request.redirect('/convenio/firma/%s' % token)
        return super().portal_agreement_submit(token, **post)

    @http.route(
        ['/convenio/descargar/<string:token>'],
        type='http',
        auth='public',
        website=True,
    )
    def portal_agreement_download(self, token, **kw):
        agreement = self._find_agreement_by_center_token(token)
        if not agreement:
            agreement = self._find_agreement_by_student_token(token)
        if not agreement or not agreement.pdf_attachment_id:
            return request.render('website.404')
        attachment = agreement.pdf_attachment_id
        filecontent = attachment.raw or (
            attachment.datas and base64.b64decode(attachment.datas)
        )
        if not filecontent:
            return request.render('website.404')
        filename = attachment.name or 'Convenio_%s.pdf' % agreement.id
        return request.make_response(
            filecontent,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )

    @http.route(
        ['/convenio/firma-alumno/<string:token>'],
        type='http',
        auth='public',
        website=True,
        sitemap=False,
    )
    def portal_agreement_student_view(self, token, **kw):
        agreement = self._find_agreement_by_student_token(token)
        if not agreement or not agreement._is_especifico():
            return request.render('website.404')
        return request.render(
            'irg_practice_agreement_specific.portal_agreement_student_page',
            {
                'agreement': agreement,
                'token': token,
                'page_name': 'convenio_firma_alumno',
                'error': kw.get('error'),
            },
        )

    @http.route(
        ['/convenio/firma-alumno/<string:token>/submit'],
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def portal_agreement_student_submit(self, token, **post):
        agreement = self._find_agreement_by_student_token(token)
        if not agreement or not agreement._is_especifico():
            return request.render('website.404')
        if agreement.state == 'completed' or agreement.signature_student:
            return request.redirect('/convenio/firma-alumno/%s' % token)
        signature_data = post.get('signature_data')
        signer_name = (post.get('student_signer_name') or '').strip()
        if not signature_data:
            return request.render(
                'irg_practice_agreement_specific.portal_agreement_student_page',
                {
                    'agreement': agreement,
                    'token': token,
                    'error': _(
                        'Debe firmar en el recuadro antes de enviar el convenio.'
                    ),
                    'page_name': 'convenio_firma_alumno',
                },
            )
        remote_ip = request.httprequest.headers.get(
            'X-Forwarded-For', request.httprequest.remote_addr
        )
        if remote_ip and ',' in remote_ip:
            remote_ip = remote_ip.split(',')[0].strip()
        agreement.action_complete_student_signature(
            signature_base64=signature_data,
            signer_name=signer_name or agreement.student_name,
            ip_address=remote_ip,
        )
        return request.redirect('/convenio/firma-alumno/%s' % token)
