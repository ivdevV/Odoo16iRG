# -*- coding: utf-8 -*-

from odoo import _
from odoo.http import request

from odoo.addons.irg_practice_preferred_quarter.controllers.main import (
    IrgPracticePreferredQuarter,
)
from odoo.addons.irg_practice_request_online_types.models.online_batch import (
    IRG_ONLINE_MASTER_PRACTICE_TYPES,
    irg_batch_code_is_online_master,
)


class IrgPracticeRequestOnlineTypes(IrgPracticePreferredQuarter):
    """Rejects disallowed practice types for online-master enrollments."""

    def _irg_create_portal_request(self, **kwargs):
        error = self._irg_online_practice_type_error(kwargs, env=request.env)
        if error:
            user_id = request.env.user.id
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
                'error_message': error,
                'form_values': kwargs,
            }
            return request.render(
                'isep_practices_2.practice_request_form_template',
                form_values,
            )
        return super()._irg_create_portal_request(**kwargs)

    def _irg_online_practice_type_error(self, kwargs, env=None):
        env = env or request.env
        course_id = kwargs.get('course_id')
        practice_center_type_id = kwargs.get('practice_center_type_id')
        if not course_id or not practice_center_type_id:
            return False
        try:
            enrollment = env['op.student.course'].sudo().browse(
                int(course_id)
            )
            practice_type = env['practice.center.type'].sudo().browse(
                int(practice_center_type_id)
            )
        except (TypeError, ValueError):
            return False
        if not enrollment.exists() or not practice_type.exists():
            return False
        batch_code = enrollment.batch_id.code if enrollment.batch_id else ''
        if not irg_batch_code_is_online_master(batch_code):
            return False
        if practice_type.type_of_practice in IRG_ONLINE_MASTER_PRACTICE_TYPES:
            return False
        return _(
            'Para másteres online solo puedes elegir convalidación '
            'por experiencia, convalidación por TFM o prácticas asíncronas.'
        )
