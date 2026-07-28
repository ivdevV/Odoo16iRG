# -*- coding: utf-8 -*-

from odoo import _
from odoo import http
from odoo.http import request

from odoo.addons.irg_practice_request_student_profile.controllers.main import (
    IrgPracticeRequestStudentProfile,
)


class IrgPracticePreferredQuarter(IrgPracticeRequestStudentProfile):
    """Añade la validación y guardado del trimestre preferente en la solicitud portal de prácticas."""

    ALLOWED_QUARTERS = (
        'marzo_mayo',
        'junio_agosto',
        'septiembre_noviembre',
        'diciembre_febrero',
    )

    def _irg_create_portal_request(self, **kwargs):
        quarter = kwargs.get('irg_preferred_quarter')
        user_id = request.env.user.id
        course_id = kwargs.get('course_id')

        if not quarter or quarter not in self.ALLOWED_QUARTERS:
            student_id = request.env['op.student'].sudo().search(
                [('user_id', '=', user_id)], limit=1
            )
            form_values = {
                'courses': request.env['op.student.course'].sudo().search(
                    [('student_id', '=', student_id.id)]
                ) if student_id else [],
                'student': student_id,
                'practice_types': request.env['practice.center.type'].sudo().search([]),
                'admissions': request.env['op.admission'].sudo().search(
                    [('student_id', '=', student_id.id)]
                ) if student_id else [],
                'error_message': _('Debes seleccionar un trimestre preferente para iniciar las prácticas.'),
                'form_values': kwargs,
            }
            return request.render(
                'isep_practices_2.practice_request_form_template',
                form_values,
            )

        res = super()._irg_create_portal_request(**kwargs)

        status_code = getattr(res, 'status_code', None)
        is_redirect = status_code and (300 <= status_code < 400)
        if is_redirect and quarter and course_id:
            try:
                course_id_int = int(course_id)
                req = request.env['practice.request'].sudo().search([
                    ('user_id', '=', user_id),
                    ('course_id', '=', course_id_int),
                ], limit=1)
                if req and req.irg_preferred_quarter != quarter:
                    req.write({'irg_preferred_quarter': quarter})
            except (ValueError, TypeError):
                pass

        return res
