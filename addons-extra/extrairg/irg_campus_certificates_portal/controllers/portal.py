# -*- coding: utf-8 -*-
import base64
import io
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.irg_gradebook_certificates.controllers.portal import (
    CertificatePortalController,
    CERTIFICATE_TYPES,
    SHIPPING_TYPES,
    CUSTOM_OPTIONS,
    PRICE_MAP,
    SHIPPING_MAP,
    PHYSICAL_TYPES,
    SIGNER_SELECTION,
)

_logger = logging.getLogger(__name__)


class IrgCampusCertificatesPortal(CertificatePortalController):

    # ------------------------------------------------------------------
    # /campus/certificates — list
    # ------------------------------------------------------------------

    @http.route(
        '/campus/certificates',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def certificate_list(self, **kw):
        partner = request.env.user.partner_id
        
        # 1. Solicitudes de certificados de notas del partner actual
        certs = request.env['irg.certificate.request'].sudo().search([
            ('partner_id', '=', partner.id),
        ], order='id desc')
        
        # 2. Estudiante(s) asociado(s) al partner actual
        students = request.env['op.student'].sudo().search([
            ('partner_id', '=', partner.id)
        ])
        
        # 3. Actas de TFM/TFG del estudiante
        actas = request.env['irg.tfm.acta'].sudo().search([
            ('student_id', 'in', students.ids),
        ], order='id desc')
        
        # 4. Diplomas válidos del estudiante
        diplomas = request.env['irg.diploma.registry'].sudo().search([
            ('student_id', 'in', students.ids),
            ('state', '=', 'valid'),
        ], order='id desc')
        
        return request.render(
            'irg_gradebook_certificates.portal_certificate_list',
            {
                'certs': certs,
                'actas': actas,
                'diplomas': diplomas,
                'page_name': 'certificates',
            },
        )

    # ------------------------------------------------------------------
    # /campus/certificates/new — request form
    # ------------------------------------------------------------------

    @http.route(
        '/campus/certificates/new',
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def certificate_new(self, **post):
        partner = request.env.user.partner_id
        
        # Load all gradebooks that are not draft or cancelled
        gradebooks = request.env['app.gradebook.student'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', 'not in', ('draft', 'cancelled')),
        ])

        # Define document types
        document_types = [
            ('gradebook', 'Certificado de Notas Completo'),
            ('gradebook_partial', 'Certificado de Notas Parcial'),
            ('diploma', 'Diploma'),
            ('attendance', 'Certificado de Asistencia'),
            ('enrollment', 'Certificado de Matrícula'),
        ]

        # ---- GET ----
        if request.httprequest.method == 'GET':
            return request.render(
                'irg_gradebook_certificates.portal_certificate_new',
                {
                    'gradebooks': gradebooks,
                    'document_types': document_types,
                    'certificate_types': CERTIFICATE_TYPES,
                    'shipping_types': SHIPPING_TYPES,
                    'custom_options': CUSTOM_OPTIONS,
                    'signer_types': SIGNER_SELECTION,
                    'price_map': PRICE_MAP,
                    'shipping_map': SHIPPING_MAP,
                    'page_name': 'certificates',
                    'error': post.get('error'),
                    'post': post,
                },
            )

        # ---- POST ----
        document_type = post.get('document_type', 'gradebook').strip()
        cert_type = post.get('certificate_type', '').strip()
        shipping_type = post.get('shipping_type', '').strip() or False
        gradebook_id = int(post.get('gradebook_id', 0) or 0)
        custom_description = post.get('custom_description', '').strip() or False
        custom_options = post.get('custom_options', '').strip() or False
        signer = post.get('signer', 'raimon').strip()
        if signer not in dict(SIGNER_SELECTION):
            signer = 'raimon'

        def _render_error(msg):
            return request.render(
                'irg_gradebook_certificates.portal_certificate_new',
                {
                    'gradebooks': gradebooks,
                    'document_types': document_types,
                    'certificate_types': CERTIFICATE_TYPES,
                    'shipping_types': SHIPPING_TYPES,
                    'custom_options': CUSTOM_OPTIONS,
                    'signer_types': SIGNER_SELECTION,
                    'price_map': PRICE_MAP,
                    'shipping_map': SHIPPING_MAP,
                    'page_name': 'certificates',
                    'error': msg,
                    'post': post,
                },
            )

        # Validate document type
        if document_type not in dict(document_types):
            return _render_error(_('Selecciona un tipo de documento válido.'))

        # Validate certificate type
        valid_types = [t[0] for t in CERTIFICATE_TYPES]
        if cert_type not in valid_types:
            return _render_error(_('Selecciona un formato de entrega válido.'))

        # Validate shipping for physical types
        if cert_type in PHYSICAL_TYPES and not shipping_type:
            return _render_error(_('El tipo de envío es obligatorio para certificados físicos.'))

        # Resolve gradebook — must belong to this user
        if gradebook_id:
            gradebook = request.env['app.gradebook.student'].sudo().browse(gradebook_id)
            if not gradebook.exists() or gradebook.partner_id.id != partner.id:
                return _render_error(_('Libreta no válida.'))
        elif len(gradebooks) == 1:
            gradebook = gradebooks[0]
        elif not gradebooks:
            return _render_error(
                _('No tienes ninguna libreta académica activa. '
                  'Contacta con administración si crees que es un error.')
            )
        else:
            return _render_error(_('Selecciona la libreta para la que solicitas el certificado.'))

        # Check state constraints for gradebook/diploma vs partial/attendance/enrollment
        if document_type in ('gradebook', 'diploma') and gradebook.state != 'done':
            return _render_error(
                _('Para solicitar este documento (Notas Completo o Diploma), '
                  'tu libreta debe estar finalizada (estado Cerrada).')
            )
        if gradebook.state in ('draft', 'cancelled'):
            return _render_error(_('La libreta seleccionada no está activa.'))

        # Enrollment payment check
        student = request.env['op.student'].sudo().search(
            [('partner_id', '=', partner.id)], limit=1
        )
        if student and hasattr(student, 'get_subscription_data'):
            sub_data = student.get_subscription_data()
            if sub_data.get('t_adeuda') or (sub_data.get('t_amount_due_data') or 0) > 0:
                return _render_error(_(
                    'No puedes solicitar un certificado mientras tengas cuotas de matrícula '
                    'pendientes de pago. Por favor, regulariza tu situación antes de continuar.'
                ))

        # Create certificate request and portal invoice
        try:
            cert = request.env['irg.certificate.request'].sudo().create({
                'gradebook_student_id': gradebook.id,
                'document_type': document_type,
                'certificate_type': cert_type,
                'shipping_type': shipping_type or False,
                'custom_description': custom_description,
                'custom_options': custom_options or False,
                'signer': signer,
                'state': 'pending_payment',
                'origin': 'portal',
            })
            cert._create_portal_invoice()
        except ValidationError as exc:
            return _render_error(exc.args[0])
        except Exception:
            _logger.exception('Error al crear la solicitud de certificado para partner %s', partner.id)
            return _render_error(_('Se ha producido un error al procesar tu solicitud. Inténtalo de nuevo.'))

        return request.redirect('/campus/certificates/confirm/%d' % cert.id)

    # ------------------------------------------------------------------
    # Download Endpoints for Diplomas and Actas (using .sudo() for safety)
    # ------------------------------------------------------------------

    @http.route(
        '/campus/certificates/download/diploma/<int:diploma_id>',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def download_diploma(self, diploma_id, **kw):
        partner = request.env.user.partner_id
        diploma = request.env['irg.diploma.registry'].sudo().browse(diploma_id)
        
        # Security: only the student associated with the logged-in partner may download
        if not diploma.exists() or diploma.student_id.partner_id.id != partner.id or diploma.state != 'valid':
            return request.redirect('/campus/certificates')
            
        if not diploma.attachment_id or not diploma.attachment_id.datas:
            return request.redirect('/campus/certificates?error=no_pdf')
            
        try:
            data = io.BytesIO(base64.standard_b64decode(diploma.attachment_id.datas))
            filename = diploma.attachment_id.name or "diploma.pdf"
            return http.send_file(data, filename=filename, as_attachment=True)
        except Exception:
            _logger.exception('Error al descargar el diploma %s', diploma_id)
            return request.redirect('/campus/certificates?error=download_error')

    @http.route(
        '/campus/certificates/download/acta/<int:acta_id>',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def download_acta(self, acta_id, **kw):
        partner = request.env.user.partner_id
        acta = request.env['irg.tfm.acta'].sudo().browse(acta_id)
        
        # Security: only the student associated with the logged-in partner may download
        if not acta.exists() or acta.student_id.partner_id.id != partner.id:
            return request.redirect('/campus/certificates')
            
        if not acta.attachment_id or not acta.attachment_id.datas:
            return request.redirect('/campus/certificates?error=no_pdf')
            
        try:
            data = io.BytesIO(base64.standard_b64decode(acta.attachment_id.datas))
            filename = acta.attachment_id.name or "acta.pdf"
            return http.send_file(data, filename=filename, as_attachment=True)
        except Exception:
            _logger.exception('Error al descargar el acta %s', acta_id)
            return request.redirect('/campus/certificates?error=download_error')
