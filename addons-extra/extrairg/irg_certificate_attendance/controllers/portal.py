# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.irg_campus_certificates_portal.controllers.portal import IrgCampusCertificatesPortal
from odoo.addons.irg_gradebook_certificates.controllers.portal import (
    CERTIFICATE_TYPES,
    SHIPPING_TYPES,
    CUSTOM_OPTIONS,
    PRICE_MAP,
    SHIPPING_MAP,
    PHYSICAL_TYPES,
    SIGNER_SELECTION,
)

_logger = logging.getLogger(__name__)

class IrgCertificateAttendancePortal(IrgCampusCertificatesPortal):

    @http.route(
        '/campus/certificates/sessions',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=True,
    )
    def get_gradebook_sessions(self, gradebook_id, **kw):
        partner = request.env.user.partner_id
        
        # Validar libreta y que pertenezca al partner del usuario
        gradebook = request.env['app.gradebook.student'].sudo().browse(int(gradebook_id))
        if not gradebook.exists() or gradebook.partner_id.id != partner.id:
            return {'error': _('Libreta no válida.')}
            
        student = request.env['op.student'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        if not student:
            return {'sessions': []}
            
        # Buscar todas las sesiones asociadas al lote (batch) de esta libreta
        sessions = request.env['op.session'].sudo().search([
            ('batch_id', '=', gradebook.batch_id.id),
        ])
        
        # Buscar las sesiones donde el alumno estuvo presente
        present_session_ids = request.env['op.attendance.line'].sudo().search([
            ('student_id', '=', student.id),
            ('present', '=', True),
            ('attendance_id.session_id', 'in', sessions.ids)
        ]).mapped('attendance_id.session_id.id')
        
        # Filtrar sesiones válidas
        valid_sessions = []
        for s in sessions:
            is_present = s.id in present_session_ids
            is_active_session = s.active and s.state in ('confirm', 'done')
            if is_present or is_active_session:
                date_class = s.start_datetime.strftime('%Y-%m-%d') if s.start_datetime else ''
                # class_title se usa preferentemente si existe (gracias a irg_op_session_class_title)
                title = getattr(s, 'class_title', '') or s.name or ''
                valid_sessions.append({
                    'id': s.id,
                    'name': s.name,
                    'class_title': title,
                    'subject_name': s.subject_id.name or '',
                    'date': date_class,
                })
        return {'sessions': valid_sessions}

    @http.route(
        '/campus/certificates/new',
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def certificate_new(self, **post):
        if request.httprequest.method == 'POST' and post.get('document_type') == 'attendance':
            partner = request.env.user.partner_id
            
            # Cargar todas las libretas académicas válidas (no borrador ni canceladas)
            gradebooks = request.env['app.gradebook.student'].sudo().search([
                ('partner_id', '=', partner.id),
                ('state', 'not in', ('draft', 'cancelled')),
            ])
            
            document_types = [
                ('gradebook', 'Certificado de Notas Completo'),
                ('gradebook_partial', 'Certificado de Notas Parcial'),
                ('diploma', 'Diploma'),
                ('attendance', 'Certificado de Asistencia'),
                ('enrollment', 'Certificado de Matrícula'),
            ]
            
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
                
            session_id = post.get('session_id')
            if not session_id:
                return _render_error(_('Debe seleccionar una sesión para el certificado de asistencia.'))
                
            gradebook_id = int(post.get('gradebook_id', 0) or 0)
            if not gradebook_id:
                return _render_error(_('Debe seleccionar la libreta académica.'))
                
            gradebook = request.env['app.gradebook.student'].sudo().browse(gradebook_id)
            if not gradebook.exists() or gradebook.partner_id.id != partner.id:
                return _render_error(_('Libreta no válida.'))
                
            # Validar si el curso/grupo es HomeClass
            has_homeclass_modality = any(m.code == 'homeclass' for m in gradebook.course_id.irg_modality_ids)
            has_hc_batch = False
            if gradebook.batch_id:
                has_hc_batch = (gradebook.batch_id.code == 'HC') or ('HC' in (gradebook.batch_id.code or '').upper()) or ('HC' in (gradebook.batch_id.name or '').upper())
            if not (has_homeclass_modality or has_hc_batch):
                return _render_error(_('El certificado de asistencia solo está disponible para cursos con modalidad HomeClass o grupos HC.'))
                
            cert_type = post.get('certificate_type', '').strip()
            shipping_type = post.get('shipping_type', '').strip() or False
            custom_description = post.get('custom_description', '').strip() or False
            custom_options = post.get('custom_options', '').strip() or False
            signer = post.get('signer', 'raimon').strip()
            if signer not in dict(SIGNER_SELECTION):
                signer = 'raimon'
                
            # Validar formato
            valid_types = [t[0] for t in CERTIFICATE_TYPES]
            if cert_type not in valid_types:
                return _render_error(_('Selecciona un formato de entrega válido.'))

            # Validar envío para tipos físicos
            if cert_type in PHYSICAL_TYPES and not shipping_type:
                return _render_error(_('El tipo de envío es obligatorio para certificados físicos.'))
                
            try:
                cert = request.env['irg.certificate.request'].sudo().create({
                    'gradebook_student_id': gradebook.id,
                    'document_type': 'attendance',
                    'session_id': int(session_id),
                    'certificate_type': cert_type,
                    'shipping_type': shipping_type or False,
                    'custom_description': custom_description,
                    'custom_options': custom_options or False,
                    'signer': signer,
                    'state': 'pending_payment',
                    'origin': 'portal',
                })
                # Crear la factura/pago portal correspondiente
                cert._create_portal_invoice()
            except ValidationError as exc:
                return _render_error(exc.args[0])
            except Exception:
                _logger.exception('Error al crear la solicitud de certificado para partner %s', partner.id)
                return _render_error(_('Se ha producido un error al procesar tu solicitud. Inténtalo de nuevo.'))
                
            return request.redirect('/campus/certificates/confirm/%d' % cert.id)
            
        return super(IrgCertificateAttendancePortal, self).certificate_new(**post)
