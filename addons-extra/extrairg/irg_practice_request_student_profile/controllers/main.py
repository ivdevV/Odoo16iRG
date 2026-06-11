# -*- coding: utf-8 -*-

from odoo import _
from odoo import http
from odoo.http import request

from odoo.addons.irg_practice_center_restrict.controllers.main import (
    IrgPracticeRequestRestrict,
)


class IrgPracticeRequestStudentProfile(IrgPracticeRequestRestrict):
    """Añade los campos de perfil del alumno al alta portal de prácticas."""

    _required_profile_fields = (
        'irg_age',
        'irg_academic_degrees',
        'irg_postgraduate_training',
        'irg_related_work_experience',
        'irg_currently_working',
        'irg_current_job_related_to_master',
        'irg_master_motivation',
        'irg_master_expectations',
        'irg_long_term_professional_goals',
        'irg_topics_to_deepen',
        'irg_future_training_interest',
    )

    @http.route()
    def create_practice_request(self, **kwargs):
        if request.httprequest.method != 'POST':
            user_id = request.env.user.id
            student = request.env['op.student'].sudo().search(
                [('user_id', '=', user_id)], limit=1
            )
            return request.render('isep_practices_2.practice_request_form_template', {
                'courses': request.env['op.student.course'].sudo().search(
                    [('student_id', '=', student.id)]
                ),
                'student': student,
                'admissions': request.env['op.admission'].sudo().search(
                    [('student_id', '=', student.id)]
                ),
                'practice_types': request.env['practice.center.type'].sudo().search([]),
                'error_message': '',
                'form_values': {},
            })
        return super().create_practice_request(**kwargs)

    def _irg_create_portal_request(self, **kwargs):
        """Replica el flujo IRG sin centro obligatorio y guarda el perfil."""
        user_id = request.env.user.id
        student_id = request.env['op.student'].sudo().search(
            [('user_id', '=', user_id)], limit=1
        )

        course_id = kwargs.get('course_id')
        op_admission_id = kwargs.get('op_admission_id')

        def _get_form_values(error=''):
            return {
                'courses': request.env['op.student.course'].sudo().search(
                    [('student_id', '=', student_id.id)]
                ),
                'student': student_id,
                'practice_types': request.env['practice.center.type'].sudo().search([]),
                'admissions': request.env['op.admission'].sudo().search(
                    [('student_id', '=', student_id.id)]
                ),
                'error_message': error,
                'form_values': kwargs,
            }

        if not course_id or not op_admission_id:
            return request.render(
                'isep_practices_2.practice_request_form_template',
                _get_form_values(error=_('Faltan datos obligatorios del formulario.')),
            )

        existing = request.env['practice.request'].sudo().search([
            ('user_id', '=', user_id),
            ('course_id', '=', int(course_id)),
        ], limit=1)

        if existing:
            return request.render(
                'isep_practices_2.practice_request_form_template',
                _get_form_values(
                    error=_('Ya tienes una solicitud en proceso. Por favor espera a que sea procesada.')
                ),
            )

        def _safe_float(value):
            try:
                return float(value) if value else 0.0
            except (TypeError, ValueError):
                return 0.0

        def _safe_int(value):
            try:
                return int(value) if value else 0
            except (TypeError, ValueError):
                return 0

        practice_center_type_id = kwargs.get('practice_center_type_id')

        missing_profile_fields = [
            field_name for field_name in self._required_profile_fields
            if not str(kwargs.get(field_name) or '').strip()
        ]
        if missing_profile_fields:
            return request.render(
                'isep_practices_2.practice_request_form_template',
                _get_form_values(
                    error=_('Debes responder todas las preguntas del perfil del alumno.')
                ),
            )

        irg_age = _safe_int(kwargs.get('irg_age'))
        if irg_age <= 0:
            return request.render(
                'isep_practices_2.practice_request_form_template',
                _get_form_values(error=_('La edad debe ser mayor que cero.')),
            )

        values = {
            'user_id': user_id,
            'name': kwargs.get('student_name'),
            'email': kwargs.get('student_email'),
            'course_id': int(course_id),
            'op_admission_id': int(op_admission_id),
            'practice_center_type_id': int(practice_center_type_id) if practice_center_type_id else False,
            'application_description': kwargs.get('application_description'),
            'country_id': int(kwargs.get('country_id')) if kwargs.get('country_id') else False,
            'state_id': int(kwargs.get('state_id')) if kwargs.get('state_id') else False,
            'zip_id': int(kwargs.get('zip_id')) if kwargs.get('zip_id') else False,
            'monday_available_start_time': _safe_float(kwargs.get('monday_available_start_time')),
            'monday_available_end_time': _safe_float(kwargs.get('monday_available_end_time')),
            'tuesday_available_start_time': _safe_float(kwargs.get('tuesday_available_start_time')),
            'tuesday_available_end_time': _safe_float(kwargs.get('tuesday_available_end_time')),
            'wednesday_available_start_time': _safe_float(kwargs.get('wednesday_available_start_time')),
            'wednesday_available_end_time': _safe_float(kwargs.get('wednesday_available_end_time')),
            'thursday_available_start_time': _safe_float(kwargs.get('thursday_available_start_time')),
            'thursday_available_end_time': _safe_float(kwargs.get('thursday_available_end_time')),
            'friday_available_start_time': _safe_float(kwargs.get('friday_available_start_time')),
            'friday_available_end_time': _safe_float(kwargs.get('friday_available_end_time')),
            'saturday_available_start_time': _safe_float(kwargs.get('saturday_available_start_time')),
            'saturday_available_end_time': _safe_float(kwargs.get('saturday_available_end_time')),
            'sunday_available_start_time': _safe_float(kwargs.get('sunday_available_start_time')),
            'sunday_available_end_time': _safe_float(kwargs.get('sunday_available_end_time')),
            'irg_age': irg_age,
            'irg_academic_degrees': kwargs.get('irg_academic_degrees'),
            'irg_postgraduate_training': kwargs.get('irg_postgraduate_training'),
            'irg_related_work_experience': kwargs.get('irg_related_work_experience'),
            'irg_currently_working': kwargs.get('irg_currently_working'),
            'irg_current_job_related_to_master': kwargs.get('irg_current_job_related_to_master') or False,
            'irg_master_motivation': kwargs.get('irg_master_motivation'),
            'irg_master_expectations': kwargs.get('irg_master_expectations'),
            'irg_long_term_professional_goals': kwargs.get('irg_long_term_professional_goals'),
            'irg_topics_to_deepen': kwargs.get('irg_topics_to_deepen'),
            'irg_future_training_interest': kwargs.get('irg_future_training_interest'),
        }

        request.env['practice.request'].sudo().create(values)
        return request.redirect('/my/practice_requests2')
