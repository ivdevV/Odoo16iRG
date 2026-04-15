# -*- coding: utf-8 -*-
from odoo import _
from odoo import http
from odoo.http import request

# Importar las clases originales de isep_practices_2 con alias para
# evitar la colisión de nombres (todos los archivos usan 'PracticeCenterPortal').
from odoo.addons.isep_practices_2.controllers.my_centers import (
    PracticeCenterPortal2,
    PracticeCenterPortal as PracticeCenterPortalCenters,
)
from odoo.addons.isep_practices_2.controllers.my_practices_request_new import (
    PracticeCenterPortal as PracticeCenterPortalRequest,
)
from odoo.addons.isep_practices_2.controllers.register_practice_center import (
    PracticeCenterPortal as PracticeCenterPortalRegister,
)


class IrgPracticeCenterCounter(PracticeCenterPortal2):
    """Sobreescribe _prepare_home_portal_values para no incluir el contador
    de centros de práctica cuando el usuario es de tipo portal (alumno).
    Evita la consulta SQL innecesaria y la entrada en el portal home."""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if request.env.user.has_group('base.group_portal'):
            values.pop('practice_centers_count', None)
        return values


class IrgPracticeCenterAccess(PracticeCenterPortalCenters):
    """Bloquea el acceso directo a las rutas de centros de práctica
    para usuarios de portal (alumnos). Devuelve 404 en lugar de mostrar
    información de centros."""

    @http.route()
    def practice_centers(self, **kw):
        if request.env.user.has_group('base.group_portal'):
            return request.not_found()
        return super().practice_centers(**kw)

    @http.route()
    def portal_practice_center(self, center_id, **kwargs):
        if request.env.user.has_group('base.group_portal'):
            return request.not_found()
        return super().portal_practice_center(center_id, **kwargs)


class IrgRegisterPracticeCenterAccess(PracticeCenterPortalRegister):
    """Bloquea el registro de nuevos centros de práctica para usuarios de
    portal (alumnos). La ruta original es 'auth=public', por lo que solo
    se bloquea cuando el usuario autenticado es de tipo portal."""

    @http.route()
    def register_practice_center(self, **kwargs):
        # Solo bloquear usuarios portal autenticados, no visitantes anónimos
        if (
            not request.env.user._is_public()
            and request.env.user.has_group('base.group_portal')
        ):
            return request.not_found()
        return super().register_practice_center(**kwargs)


class IrgPracticeRequestRestrict(PracticeCenterPortalRequest):
    """Sobreescribe create_practice_request para que los usuarios de portal
    (alumnos) puedan enviar solicitudes de práctica sin tener que seleccionar
    un centro. El coordinador asignará el centro manualmente desde el backend.

    Solo el flujo POST se modifica para portal users. El GET (renderizar el
    formulario) sigue delegando al padre, de modo que el template override
    (views/templates.xml) se encarga de ocultar los checkboxes de centros.
    """

    @http.route()
    def create_practice_request(self, **kwargs):
        if (
            request.httprequest.method == 'POST'
            and request.env.user.has_group('base.group_portal')
        ):
            return self._irg_create_portal_request(**kwargs)
        return super().create_practice_request(**kwargs)

    def _irg_create_portal_request(self, **kwargs):
        """Lógica POST para usuarios de portal: omite la validación de
        centros de práctica y crea la solicitud sin solicited_practice_center_ids.
        """
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
            }

        if not course_id or not op_admission_id:
            return request.render(
                'isep_practices_2.practice_request_form_template',
                _get_form_values(error=_('Faltan datos obligatorios del formulario.')),
            )

        # Verificar si ya existe una solicitud en proceso para este curso
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

        practice_center_type_id = kwargs.get('practice_center_type_id')

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
            # Horarios disponibles del alumno
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
            # NO se incluyen solicited_practice_center_ids ni practice_center_id.
            # El coordinador los asignará manualmente desde el backend.
        }

        request.env['practice.request'].sudo().create(values)
        return request.redirect('/my/practice_requests2')
