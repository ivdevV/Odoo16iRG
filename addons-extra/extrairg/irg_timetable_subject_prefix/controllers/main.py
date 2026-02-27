# -*- coding: utf-8 -*-
from pytz import timezone

from odoo import http
from odoo.http import request


class IrgTimeTablePortalPrefix(http.Controller):

    @http.route('/get-timetable/data', type='json', auth='user', website=True)
    def get_timetable_data_portal(self, stud_id=None, current_timezone=None):
        data = []
        course_list = []
        batch_list = []

        if stud_id:
            student = request.env['op.student'].sudo().search([
                ('id', '=', int(stud_id))
            ])
        else:
            student = request.env['op.student'].sudo().search([
                ('user_id', '=', request.env.uid)
            ])

        for course in student.course_detail_ids:
            course_list.append(course.course_id.id)
            batch_list.append(course.batch_id.id)

        session_model = request.env['op.session'].sudo().search([
            ('course_id', 'in', course_list),
            ('batch_id', 'in', batch_list),
        ])

        user_tz = request.env.user.tz or current_timezone or 'UTC'
        for session in session_model:
            lesson_text = ''.join(session.lesson_ids.mapped('lesson_topic'))
            row = {
                'title': session.subject_id.display_name or session.subject_id.name,
                'start': session.start_datetime.astimezone(timezone(user_tz)),
                'end': session.end_datetime.astimezone(timezone(user_tz)),
                'faculty': session.faculty_id.name,
                'batch': session.batch_id.name,
                'course': session.course_id.name,
                'day': session.type,
                'time': session.timing,
                'lesson': lesson_text,
            }

            if 'time_url_metting' in session._fields:
                row['time_url_metting'] = session.time_url_metting
            if 'time_url_recoding' in session._fields:
                row['time_url_recoding'] = session.time_url_recoding

            data.append(row)

        return data
