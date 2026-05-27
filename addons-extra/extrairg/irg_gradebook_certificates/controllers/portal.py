# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

from ..models.irg_certificate_request import (
    CERTIFICATE_TYPES,
    SHIPPING_TYPES,
    CUSTOM_OPTIONS,
    PRICE_MAP,
    SHIPPING_MAP,
    PHYSICAL_TYPES,
    SIGNER_SELECTION,
)

_logger = logging.getLogger(__name__)

PRODUCT_XMLIDS = {
    'digital': 'irg_gradebook_certificates.product_cert_digital',
    'physical': 'irg_gradebook_certificates.product_cert_physical',
    'custom': 'irg_gradebook_certificates.product_cert_custom',
    'physical_apostilled': 'irg_gradebook_certificates.product_cert_apostilled',
}

SHIPPING_PRODUCT_XMLIDS = {
    'national': 'irg_gradebook_certificates.product_shipping_national',
    'international': 'irg_gradebook_certificates.product_shipping_international',
}


def _get_portal_gradebooks():
    """Return closed (state=done) gradebooks belonging to the current portal user.

    Only closed libretas are eligible for certificate requests.
    """
    partner = request.env.user.partner_id
    return request.env['app.gradebook.student'].sudo().search([
        ('partner_id', '=', partner.id),
        ('state', '=', 'done'),
    ])


def _build_sale_order(cert, partner):
    """Create and return a new sale.order for the given certificate request."""
    cert_product_tmpl = request.env.ref(PRODUCT_XMLIDS[cert.certificate_type]).sudo()
    cert_product = cert_product_tmpl.product_variant_ids[:1]
    if not cert_product:
        raise ValidationError(_('El producto del certificado no está configurado.'))

    order_lines = [(0, 0, {
        'product_id': cert_product.id,
        'product_uom_qty': 1,
        'price_unit': PRICE_MAP.get(cert.certificate_type, 0.0),
        'name': cert_product_tmpl.name,
    })]

    if cert.shipping_type and cert.certificate_type in PHYSICAL_TYPES:
        ship_tmpl = request.env.ref(SHIPPING_PRODUCT_XMLIDS[cert.shipping_type]).sudo()
        ship_product = ship_tmpl.product_variant_ids[:1]
        if ship_product:
            order_lines.append((0, 0, {
                'product_id': ship_product.id,
                'product_uom_qty': 1,
                'price_unit': SHIPPING_MAP.get(cert.shipping_type, 0.0),
                'name': ship_tmpl.name,
            }))

    sale_order = request.env['sale.order'].sudo().create({
        'partner_id': partner.id,
        'order_line': order_lines,
        'certificate_request_id': cert.id,
        'note': _('Certificado de notas %s — referencia %s') % (
            dict(CERTIFICATE_TYPES).get(cert.certificate_type, ''), cert.name
        ),
    })
    return sale_order


class CertificatePortalController(http.Controller):

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
        certs = request.env['irg.certificate.request'].sudo().search([
            ('partner_id', '=', partner.id),
        ], order='id desc')
        return request.render(
            'irg_gradebook_certificates.portal_certificate_list',
            {
                'certs': certs,
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
        gradebooks = _get_portal_gradebooks()

        # ---- GET ----
        if request.httprequest.method == 'GET':
            return request.render(
                'irg_gradebook_certificates.portal_certificate_new',
                {
                    'gradebooks': gradebooks,
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

        # Validate certificate type
        valid_types = [t[0] for t in CERTIFICATE_TYPES]
        if cert_type not in valid_types:
            return _render_error(_('Selecciona un tipo de certificado válido.'))

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
                _('No tienes ninguna libreta académica cerrada. '
                  'Solo puedes solicitar certificados cuando tu libreta de calificaciones '
                  'esté finalizada. Contacta con administración si crees que es un error.')
            )
        else:
            return _render_error(_('Selecciona la libreta para la que solicitas el certificado.'))

        # Enrollment payment check — only for students with an active subscription.
        # If the student has no op.student record the check is skipped gracefully.
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
    # /campus/certificates/confirm/<id> — confirmation page
    # ------------------------------------------------------------------

    @http.route(
        '/campus/certificates/confirm/<int:cert_id>',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def certificate_confirm(self, cert_id, **kw):
        cert = request.env['irg.certificate.request'].sudo().browse(cert_id)
        partner = request.env.user.partner_id
        if not cert.exists() or cert.partner_id.id != partner.id:
            return request.redirect('/campus/certificates')
        return request.render(
            'irg_gradebook_certificates.portal_certificate_confirm',
            {
                'cert': cert,
                'page_name': 'certificates',
            },
        )

    # ------------------------------------------------------------------
    # /campus/certificates/download/<id> — PDF download
    # ------------------------------------------------------------------

    @http.route(
        '/campus/certificates/download/<int:cert_id>',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def certificate_download(self, cert_id, **kw):
        partner = request.env.user.partner_id
        cert = request.env['irg.certificate.request'].sudo().browse(cert_id)

        # Security: only the owning student may download
        if not cert.exists() or cert.partner_id.id != partner.id:
            return request.redirect('/campus/certificates')

        # Not yet paid — take the student back to the confirm page with the payment link
        if cert.state == 'pending_payment':
            return request.redirect('/campus/certificates/confirm/%d' % cert.id)

        if not cert.attachment_id:
            return request.redirect('/campus/certificates?error=no_pdf')

        # Serve the attachment directly
        return request.redirect(
            '/web/content/%d?download=true' % cert.attachment_id.id
        )
