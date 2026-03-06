# -*- coding: utf-8 -*-
from pytz import timezone

from odoo import http
from odoo.http import request


class IrgTimeTablePortalPrefix(http.Controller):

    def _get_student_scope(self, student):
        """Collect all batch/course ids assigned to the student through supported links."""
        batch_ids = set(student.course_detail_ids.mapped('batch_id').ids)
        course_ids = set(student.course_detail_ids.mapped('course_id').ids)

        User = request.env['res.users'].sudo()
        StudentCourse = request.env['op.student.course'].sudo()
        Admission = request.env['op.admission'].sudo()

        user = User.search([('partner_id', '=', student.partner_id.id)], limit=1)

        if user and 'op_batch_ids' in user._fields:
            user_batches = user.op_batch_ids
            batch_ids.update(user_batches.ids)
            if 'course_id' in request.env['op.batch']._fields:
                course_ids.update(user_batches.mapped('course_id').ids)

        sc_domain = [('student_id', '=', student.id)]
        if 'batch_id' in StudentCourse._fields:
            batch_ids.update(StudentCourse.search(sc_domain + [('batch_id', '!=', False)]).mapped('batch_id').ids)
        if 'course_id' in StudentCourse._fields:
            course_ids.update(StudentCourse.search(sc_domain + [('course_id', '!=', False)]).mapped('course_id').ids)

        adm_domain = [('partner_id', '=', student.partner_id.id)]
        if 'batch_id' in Admission._fields:
            batch_ids.update(Admission.search(adm_domain + [('batch_id', '!=', False)]).mapped('batch_id').ids)
        if 'course_id' in Admission._fields:
            course_ids.update(Admission.search(adm_domain + [('course_id', '!=', False)]).mapped('course_id').ids)

        return list(course_ids), list(batch_ids)

    @http.route('/get-timetable/data', type='json', auth='user', website=True)
    def get_timetable_data_portal(self, stud_id=None, current_timezone=None):
        data = []

        if stud_id:
            student = request.env['op.student'].sudo().search([
                ('id', '=', int(stud_id))
            ])
        else:
            student = request.env['op.student'].sudo().search([
                ('user_id', '=', request.env.uid)
            ])

        course_ids = set()
        batch_ids = set()
        for student_rec in student:
            current_course_ids, current_batch_ids = self._get_student_scope(student_rec)
            course_ids.update(current_course_ids)
            batch_ids.update(current_batch_ids)

        if batch_ids:
            session_domain = [('batch_id', 'in', list(batch_ids))]
        elif course_ids:
            session_domain = [('course_id', 'in', list(course_ids))]
        else:
            return data

        session_model = request.env['op.session'].sudo().search(session_domain)

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
