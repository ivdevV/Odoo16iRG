# -*- coding: utf-8 -*-
import base64
import io
import logging

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrgDiplomadoPortalRequestController(http.Controller):
    def _get_portal_student(self):
        partner = request.env.user.partner_id
        return request.env['op.student'].sudo().search([
            ('partner_id', '=', partner.id),
        ], limit=1)

    def _get_gradebook(self, course, student):
        partner = request.env.user.partner_id
        domain = [
            ('partner_id', '=', partner.id),
            ('course_id', '=', course.id),
            ('state', '=', 'done'),
        ]
        gradebook = request.env['app.gradebook.student'].sudo().search(domain, order='id desc', limit=1)
        if not gradebook and student:
            gradebook = request.env['app.gradebook.student'].sudo().search([
                ('student_id', '=', student.id),
                ('course_id', '=', course.id),
                ('state', '=', 'done'),
            ], order='id desc', limit=1)
        return gradebook

    def _get_page_values(self, course_id):
        course = request.env['op.course'].sudo().browse(course_id)
        student = self._get_portal_student()
        values = {
            'course': course,
            'student': student,
            'gradebook': request.env['app.gradebook.student'].sudo(),
            'final_grade': 0.0,
            'eligible': False,
            'diplomado_request': request.env['irg.diplomado.portal.request'].sudo(),
            'diplomado_registry': request.env['irg.diplomado.registry'].sudo(),
            'error': False,
            'success': False,
            'page_name': 'diplomado_portal_request',
        }

        if not course.exists() or not course.irg_is_diplomado():
            values['error'] = _('Este curso no corresponde a un diplomado.')
            return values
        if not student:
            values['error'] = _('No se encontro un alumno asociado a tu usuario.')
            return values

        gradebook = self._get_gradebook(course, student)
        final_grade = gradebook.total_final if gradebook else 0.0
        eligible = bool(gradebook and final_grade > 7.0)
        diplomado_registry = request.env['irg.diplomado.registry'].sudo().search([
            ('student_id', '=', student.id),
            ('course_id', '=', course.id),
        ], order='id desc', limit=1)
        diplomado_request = request.env['irg.diplomado.portal.request'].sudo().search([
            ('student_id', '=', student.id),
            ('course_id', '=', course.id),
            ('state', 'in', ('requested', 'processed')),
        ], order='id desc', limit=1)

        values.update({
            'gradebook': gradebook,
            'final_grade': final_grade,
            'eligible': eligible,
            'diplomado_registry': diplomado_registry,
            'diplomado_request': diplomado_request,
        })
        if request.params.get('success') == '1':
            values['success'] = _('Diploma generado correctamente.')
        elif request.params.get('error') == 'grade_too_low':
            values['error'] = _('Solo puedes solicitar el diploma si tu calificacion final es superior a 7.0.')
        elif request.params.get('error') == 'already_requested':
            values['error'] = _('Este diploma ya esta solicitado o emitido.')
        elif request.params.get('error') == 'no_pdf':
            values['error'] = _('El PDF del diploma todavia no esta disponible.')
        elif not gradebook:
            values['error'] = _('El diplomado todavia no consta como completado.')
        elif not eligible:
            values['error'] = _('Tu calificacion final no supera el minimo requerido de 7.0.')
        return values

    @http.route('/campus/diplomados/<int:course_id>', type='http', auth='user', website=True, methods=['GET'])
    def diplomado_page(self, course_id, **kw):
        values = self._get_page_values(course_id)
        return request.render('irg_diplomado_portal_request.portal_diplomado_page', values)

    @http.route('/campus/diplomados/<int:course_id>/request', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def request_diplomado(self, course_id, **post):
        values = self._get_page_values(course_id)
        course = values['course']
        student = values['student']
        gradebook = values['gradebook']
        redirect_url = '/campus/diplomados/%s' % course_id

        if not course.exists() or not course.irg_is_diplomado() or not student:
            return request.redirect(redirect_url)
        if not gradebook or not values['eligible']:
            return request.redirect('%s?error=grade_too_low' % redirect_url)

        diplomado = values['diplomado_registry'] or self._create_diplomado_registry(student, course, gradebook)
        return self._send_diplomado_file(diplomado)

    def _create_diplomado_registry(self, student, course, gradebook):
        batch = gradebook.batch_id
        return request.env['irg.diplomado.registry'].sudo().create({
            'student_id': student.id,
            'student_name': student.name,
            'course_id': course.id,
            'diplomado_name': course.name,
            'start_date': batch.start_date if batch else False,
            'end_date': batch.end_date if batch else False,
            'diploma_type': 'digital',
            'subjects_presencial': course.irg_diplomado_subjects_presencial or '',
            'subjects_online': course.irg_diplomado_subjects_online or '',
        })

    @http.route('/campus/diplomados/download/<int:registry_id>', type='http', auth='user', website=True, methods=['GET'])
    def download_diplomado(self, registry_id, **kw):
        partner = request.env.user.partner_id
        diplomado = request.env['irg.diplomado.registry'].sudo().browse(registry_id)
        if not diplomado.exists() or diplomado.student_id.partner_id.id != partner.id:
            return request.redirect('/my')
        if not diplomado.course_id.irg_is_diplomado():
            return request.redirect('/my')

        gradebook = self._get_gradebook(diplomado.course_id, diplomado.student_id)
        if not gradebook or gradebook.total_final <= 7.0:
            return request.redirect('/campus/diplomados/%s?error=grade_too_low' % diplomado.course_id.id)

        return self._send_diplomado_file(diplomado)

    def _send_diplomado_file(self, diplomado):
        if not diplomado.attachment_id or not diplomado.attachment_id.datas:
            try:
                diplomado.action_reprint()
            except Exception:
                _logger.exception('Error al generar el PDF del diplomado %s', diplomado.id)
                return request.redirect('/campus/diplomados/%s?error=no_pdf' % diplomado.course_id.id)

        if not diplomado.attachment_id or not diplomado.attachment_id.datas:
            return request.redirect('/campus/diplomados/%s?error=no_pdf' % diplomado.course_id.id)

        try:
            data = io.BytesIO(base64.standard_b64decode(diplomado.attachment_id.datas))
            filename = diplomado.attachment_id.name or 'diplomado.pdf'
            return http.send_file(data, filename=filename, as_attachment=True)
        except Exception:
            _logger.exception('Error al descargar el diplomado %s', registry_id)
            return request.redirect('/campus/diplomados/%s?error=no_pdf' % diplomado.course_id.id)
