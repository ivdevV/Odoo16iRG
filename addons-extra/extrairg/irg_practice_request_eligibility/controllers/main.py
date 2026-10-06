# -*- coding: utf-8 -*-

from odoo import _
from odoo import http
from odoo.http import request

from odoo.addons.irg_practice_request_online_types.controllers.main import (
    IrgPracticeRequestOnlineTypes,
)
from odoo.addons.isep_practices_2.controllers.my_practice_request2 import (
    PracticeCenterPortal as PracticeRequestListPortal,
)


class IrgPracticeRequestEligibility(IrgPracticeRequestOnlineTypes):
    """Reject portal practice requests below 50% or for diplomado courses."""

    def _irg_create_portal_request(self, **kwargs):
        error = self._irg_practice_eligibility_error(kwargs, env=request.env)
        if error:
            user_id = request.env.user.id
            student = request.env['op.student'].sudo().search(
                [('user_id', '=', user_id)], limit=1
            )
            return request.render(
                'isep_practices_2.practice_request_form_template',
                {
                    'courses': request.env['op.student.course'].sudo().search(
                        [('student_id', '=', student.id)]
                    ) if student else request.env['op.student.course'],
                    'student': student,
                    'practice_types': request.env['practice.center.type'].sudo().search([]),
                    'admissions': request.env['op.admission'].sudo().search(
                        [('student_id', '=', student.id)]
                    ) if student else request.env['op.admission'],
                    'error_message': error,
                    'form_values': kwargs,
                },
            )
        return super()._irg_create_portal_request(**kwargs)

    def _irg_practice_eligibility_error(self, kwargs, env=None):
        env = env or request.env
        course_id = kwargs.get('course_id')
        if not course_id:
            return False
        try:
            enrollment = env['op.student.course'].sudo().browse(int(course_id))
        except (TypeError, ValueError):
            return False
        if not enrollment.exists():
            return False
        admission = env['op.admission']
        admission_id = kwargs.get('op_admission_id')
        if admission_id:
            try:
                admission = env['op.admission'].sudo().browse(int(admission_id))
            except (TypeError, ValueError):
                admission = env['op.admission']
            if not admission.exists():
                admission = env['op.admission']
        if env.user.has_group('base.group_portal'):
            if (
                not enrollment.student_id
                or enrollment.student_id.user_id != env.user
            ):
                return _(
                    'No puedes solicitar prácticas para una matrícula que no es tuya.'
                )
            if admission and admission.student_id != enrollment.student_id:
                return _(
                    'La admisión no corresponde al alumno de la matrícula.'
                )
        reason = enrollment.irg_practice_request_block_reason()
        if reason == 'diplomado' or (
            admission
            and admission.exists()
            and admission.course_id
            and admission.course_id.irg_excludes_practice_request()
        ):
            return _('Los diplomados no incluyen solicitud de prácticas.')
        if reason:
            return _(
                'Puedes solicitar prácticas cuando el avance del curso '
                'llegue al 50% de las asignaturas obligatorias.'
            )
        if (
            admission
            and admission.course_id
            and admission.course_id != enrollment.course_id
        ):
            return _('La matrícula no corresponde al curso seleccionado.')
        return False


class IrgPracticeRequestEligibilityList(PracticeRequestListPortal):
    """Hide the new-request button until one enrollment is eligible."""

    @http.route()
    def list_practice_requests(self, **kwargs):
        user = request.env.user
        student = request.env['op.student'].sudo().search(
            [('user_id', '=', user.id)], limit=1
        )
        practice_requests = request.env['practice.request'].sudo().search([
            ('user_id', '=', user.id),
        ])
        return request.render(
            'isep_practices_2.practice_request_portal_template',
            {
                'practice_requests': practice_requests,
                'irg_can_request_practice': bool(
                    student and student.irg_can_request_any_practice()
                ),
            },
        )
