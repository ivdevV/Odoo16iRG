# -*- coding: utf-8 -*-
import base64
import io
import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.irg_campus_certificates_portal.controllers.portal import IrgCampusCertificatesPortal

_logger = logging.getLogger(__name__)


class IrgCampusDiplomadosPortal(IrgCampusCertificatesPortal):

    @http.route(
        '/campus/certificates',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def certificate_list(self, **kw):
        response = super(IrgCampusDiplomadosPortal, self).certificate_list(**kw)
        
        # Si la respuesta es de tipo render (QWeb template) y tiene qcontext
        if hasattr(response, 'qcontext'):
            partner = request.env.user.partner_id
            
            # Estudiante(s) asociado(s) al partner actual
            students = request.env['op.student'].sudo().search([
                ('partner_id', '=', partner.id)
            ])
            
            # Buscar todos los diplomados vinculados a estos estudiantes
            diplomados_raw = request.env['irg.diplomado.registry'].sudo().search([
                ('student_id', 'in', students.ids),
            ], order='id desc')
            
            diplomados_data = []
            for d in diplomados_raw:
                # Buscar la libreta académica correspondiente
                gradebook = request.env['app.gradebook.student'].sudo().search([
                    ('student_id', '=', d.student_id.id),
                    ('course_id', '=', d.course_id.id),
                ], limit=1)
                
                final_grade = gradebook.total_final if gradebook else 0.0
                can_download = final_grade > 7.0
                
                # Adjuntamos datos dinámicos al objeto en memoria para consumirlos en QWeb
                d_info = {
                    'record': d,
                    'final_grade': final_grade,
                    'can_download': can_download,
                }
                diplomados_data.append(d_info)
                
            response.qcontext['diplomados_data'] = diplomados_data
            
        return response

    @http.route(
        '/campus/certificates/new',
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def certificate_new(self, **post):
        # Si es un POST y el gradebook seleccionado corresponde a un diplomado, bloqueamos la solicitud
        if request.httprequest.method == 'POST':
            gradebook_id = int(post.get('gradebook_id', 0) or 0)
            if gradebook_id:
                gradebook = request.env['app.gradebook.student'].sudo().browse(gradebook_id)
                if gradebook.exists() and gradebook.course_id.is_diplomado():
                    post['gradebook_id'] = '0'  # Provocará error de libreta no válida o no seleccionada en el super()

        # Llamar al controlador original
        response = super(IrgCampusDiplomadosPortal, self).certificate_new(**post)

        # Filtrar los diplomados del listado de gradebooks que se muestra en el combo
        if hasattr(response, 'qcontext') and 'gradebooks' in response.qcontext:
            gradebooks = response.qcontext['gradebooks']
            response.qcontext['gradebooks'] = gradebooks.filtered(lambda gb: not gb.course_id.is_diplomado())

        return response

    @http.route(
        '/campus/certificates/download/diplomado/<int:diplomado_id>',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def download_diplomado(self, diplomado_id, **kw):
        partner = request.env.user.partner_id
        diplomado = request.env['irg.diplomado.registry'].sudo().browse(diplomado_id)
        
        # Seguridad: verificar que existe, pertenece al partner
        if not diplomado.exists() or diplomado.student_id.partner_id.id != partner.id:
            return request.redirect('/campus/certificates')
            
        # Comprobar calificación final > 7.0 en la libreta académica
        gradebook = request.env['app.gradebook.student'].sudo().search([
            ('student_id', '=', diplomado.student_id.id),
            ('course_id', '=', diplomado.course_id.id),
        ], limit=1)
        
        if not gradebook or gradebook.total_final <= 7.0:
            return request.redirect('/campus/certificates?error=grade_too_low')
            
        # Si no tiene attachment_id o datas válidos, intentamos regenerarlo
        if not diplomado.attachment_id or not diplomado.attachment_id.datas:
            try:
                diplomado.action_reprint()
            except Exception:
                _logger.exception('Error al regenerar el PDF del diplomado %s', diplomado_id)
                return request.redirect('/campus/certificates?error=no_pdf')
                
        if not diplomado.attachment_id or not diplomado.attachment_id.datas:
            return request.redirect('/campus/certificates?error=no_pdf')
            
        try:
            data = io.BytesIO(base64.standard_b64decode(diplomado.attachment_id.datas))
            filename = diplomado.attachment_id.name or "diplomado.pdf"
            return http.send_file(data, filename=filename, as_attachment=True)
        except Exception:
            _logger.exception('Error al descargar el diplomado %s', diplomado_id)
            return request.redirect('/campus/certificates?error=download_error')
