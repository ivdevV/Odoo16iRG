# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

from odoo.addons.irg_course_portal_tiles.controllers.portal_overrides import (
    IrgCoursePortalOverrides,
)
from odoo.addons.isep_time_link_url.controller.main import TimeTablePortalURl

_logger = logging.getLogger(__name__)


class IrgProfileBatchFixCourseOverride(IrgCoursePortalOverrides):
    """
    Hereda el controller de irg_course_portal_tiles para inyectar
    student_batch_id en el contexto de la vista de curso.

    Este valor le permite a la plantilla del tile de calendario construir
    un href con ?batch_id=X, de modo que el calendario filtre solo las
    sesiones del batch del alumno para ese curso.

    No llamamos a super() porque el padre hace el render directo. En su lugar
    replicamos su lógica completa y añadimos la búsqueda del batch, luego
    hacemos nosotros el render final.
    """

    @http.route(['/campus/course/<int:course_id>'], type='http', auth="user", website=True)
    def view_user_profile_course(self, course_id, **post):
        user_id = request.env.user.id
        user = self._check_user_profile_access(user_id)
        if not user:
            return request.render("website_profile.private_profile")

        values = self._prepare_user_values(**post)
        params = self._prepare_user_profile_parameters(**post)
        values.update(self._prepare_user_profile_values(user, **params))

        values['op_course_id'] = course_id

        # Buscar el batch del alumno para este curso específico.
        # Si el URL incluye ?batch_id=X (caso de 2 admisiones en el mismo curso),
        # usamos ese valor directamente para evitar ambigüedad.
        student = request.env['op.student'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1
        )
        student_batch_id = False
        batch_id_param = post.get('batch_id')
        if student:
            if batch_id_param:
                try:
                    student_batch_id = int(batch_id_param)
                except (ValueError, TypeError):
                    pass
            if not student_batch_id:
                course_detail = student.course_detail_ids.filtered(
                    lambda cd: cd.course_id.id == course_id
                )
                if course_detail:
                    student_batch_id = course_detail[0].batch_id.id

        values['student_batch_id'] = student_batch_id

        # Replicar el filtro de menú del módulo padre
        menu_list = request.env['openeducat.portal.menu'].sudo().search([
            ('is_visible_to_student', '=', True)
        ])

        def _is_course_tool_local(menu):
            name = (menu.name or '').lower()
            for kw in ('calendar', 'calendario', 'practic', 'práctic', 'prácticas', 'practica'):
                if kw in name:
                    return True
            return False

        def _is_hidden_badge(menu):
            name = (menu.name or '').lower()
            for kw in ('badge', 'insign', 'insignia', 'insignias'):
                if kw in name:
                    return True
            return False

        values['menu_list'] = menu_list.filtered(
            lambda m: _is_course_tool_local(m) and not _is_hidden_badge(m)
        )

        _logger.debug(
            'IRG BATCH FIX: course_id=%s student_batch_id=%s',
            course_id, student_batch_id,
        )
        return request.render("isep_website_custom.user_profile_course", values)


class IrgProfileBatchFixTimetableOverride(TimeTablePortalURl):
    """
    Hereda el controller de isep_time_link_url para aceptar un parámetro
    batch_id opcional. Cuando se proporciona, filtra las sesiones solo al
    batch indicado, evitando que el calendario muestre sesiones de otros
    programas del mismo alumno.
    """

    @http.route('/get-timetable/data', type='json', auth='user', website=True)
    def get_timetable_data_portal(self, stud_id=None, current_timezone=None, batch_id=None):
        from pytz import timezone as tz_convert

        data = []
        course_list = []
        batch_list = []

        if stud_id:
            student = request.env['op.student'].sudo().search(
                [('id', '=', int(stud_id))]
            )
        else:
            student = request.env['op.student'].sudo().search(
                [('user_id', '=', request.env.uid)]
            )

        for course in student.course_detail_ids:
            course_list.append(course.course_id.id)
            batch_list.append(course.batch_id.id)

        session_domain = [
            ('course_id', 'in', course_list),
            ('batch_id', 'in', batch_list),
        ]
        if batch_id:
            session_domain.append(('batch_id', '=', int(batch_id)))

        session_model = request.env['op.session'].sudo().search(session_domain)
        user_tz = request.env.user.tz or current_timezone or 'UTC'

        for session in session_model:
            all_lession = ''
            for lesson in session.lesson_ids:
                all_lession += lesson.lesson_topic
            data.append({
                'title': session.subject_id.name,
                'start': session.start_datetime.astimezone(tz_convert(user_tz)),
                'end': session.end_datetime.astimezone(tz_convert(user_tz)),
                'faculty': session.faculty_id.name,
                'batch': session.batch_id.name,
                'course': session.course_id.name,
                'day': session.type,
                'time': session.timing,
                'lesson': all_lession,
                'time_url_metting': session.time_url_metting,
                'time_url_recoding': session.time_url_recoding,
            })

        _logger.debug(
            'IRG BATCH FIX timetable: batch_id=%s sessions=%d',
            batch_id, len(data),
        )
        return data
