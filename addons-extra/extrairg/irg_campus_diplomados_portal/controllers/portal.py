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
            
            # Buscar todas las solicitudes de diplomados
            solicitudes = request.env['irg.diplomado.request'].sudo().search([
                ('student_id', 'in', students.ids),
            ], order='id desc')
            
            # Buscar libretas académicas finalizadas del alumno
            gradebooks_diplomados = request.env['app.gradebook.student'].sudo().search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'done'),
            ])
            
            # Filtrar libretas que correspondan a diplomados y que tengan nota > 7.0
            gradebooks_diplomados = gradebooks_diplomados.filtered(
                lambda gb: gb.course_id.is_diplomado() and gb.total_final > 7.0
            )
            
            # 1. Poblamos datos de diplomados emitidos
            diplomados_data = []
            for d in diplomados_raw:
                gradebook = request.env['app.gradebook.student'].sudo().search([
                    ('student_id', '=', d.student_id.id),
                    ('course_id', '=', d.course_id.id),
                ], limit=1)
                
                final_grade = gradebook.total_final if gradebook else 0.0
                can_download = final_grade > 7.0
                
                diplomados_data.append({
                    'record': d,
                    'final_grade': final_grade,
                    'can_download': can_download,
                })
                
            # 2. Poblamos solicitudes en trámite
            solicitudes_tramite = solicitudes.filtered(lambda r: r.state == 'requested')
            
            # 3. Poblamos cursos disponibles para solicitar (libreta con nota > 7, sin diploma ni solicitud activa)
            disponibles_solicitar = []
            for gb in gradebooks_diplomados:
                has_diploma = any(d.course_id.id == gb.course_id.id for d in diplomados_raw)
                has_request = any(r.course_id.id == gb.course_id.id and r.state in ('requested', 'processed') for r in solicitudes)
                if not has_diploma and not has_request:
                    disponibles_solicitar.append(gb)
                    
            # 4. Visibilidad Contextual y Filtrado por course_id
            course_id = kw.get('course_id')
            only_diplomados = False
            if course_id:
                try:
                    course = request.env['op.course'].sudo().browse(int(course_id))
                    if course.exists() and course.is_diplomado():
                        only_diplomados = True
                        # Filtrar datos exclusivamente para este curso
                        diplomados_data = [d for d in diplomados_data if d['record'].course_id.id == course.id]
                        solicitudes_tramite = solicitudes_tramite.filtered(lambda r: r.course_id.id == course.id)
                        disponibles_solicitar = [gb for gb in disponibles_solicitar if gb.course_id.id == course.id]
                except Exception:
                    pass
                    
            # Pasar variables al contexto de la plantilla
            response.qcontext.update({
                'diplomados_data': diplomados_data,
                'solicitudes_tramite': solicitudes_tramite,
                'disponibles_solicitar': disponibles_solicitar,
                'only_diplomados': only_diplomados,
            })
            
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
        '/campus/certificates/request/diplomado/<int:course_id>',
        type='http',
        auth='user',
        website=True,
        methods=['POST', 'GET'],
        csrf=True,
    )
    def request_diplomado(self, course_id, **kw):
        partner = request.env.user.partner_id
        student = request.env['op.student'].sudo().search([
            ('partner_id', '=', partner.id)
        ], limit=1)
        
        if not student:
            return request.redirect('/campus/certificates')
            
        # Comprobar libreta finalizada y nota > 7.0
        gradebook = request.env['app.gradebook.student'].sudo().search([
            ('student_id', '=', student.id),
            ('course_id', '=', course_id),
            ('state', '=', 'done')
        ], limit=1)
        
        if not gradebook or gradebook.total_final <= 7.0:
            return request.redirect(f'/campus/certificates?course_id={course_id}&error=grade_too_low')
            
        # Verificar duplicados (si ya hay diploma o solicitud activa)
        has_diploma = request.env['irg.diplomado.registry'].sudo().search_count([
            ('student_id', '=', student.id),
            ('course_id', '=', course_id)
        ]) > 0
        
        has_request = request.env['irg.diplomado.request'].sudo().search_count([
            ('student_id', '=', student.id),
            ('course_id', '=', course_id),
            ('state', 'in', ('requested', 'processed'))
        ]) > 0
        
        if has_diploma or has_request:
            return request.redirect(f'/campus/certificates?course_id={course_id}&error=already_requested')
            
        # Crear la solicitud
        request.env['irg.diplomado.request'].sudo().create({
            'student_id': student.id,
            'course_id': course_id,
            'state': 'requested',
        })
        
        # Redirigir al campus con éxito, preservando el contexto del curso si aplica
        return request.redirect(f'/campus/certificates?course_id={course_id}&request_success=1')

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
