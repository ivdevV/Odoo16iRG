# -*- coding: utf-8 -*-
from . import api_serializer as ser


class MoodleService:

    def __init__(self, env):
        self.env = env

    def get_moodle_sync_status(self, payload):
        if 'irg.moodle.grade' not in self.env:
            return {
                'available': False,
                'maps': 0,
                'grades': 0,
                'unmatched': 0,
                'last_sync': False,
            }
        map_domain = []
        grade_domain = []
        if payload.get('course_id') and 'irg.moodle.subject.map' in self.env:
            Map = self.env['irg.moodle.subject.map']
            if 'subject_id' in Map._fields:
                course = self.env['op.course'].browse(ser.require_positive_id(payload, 'course_id'))
                map_domain.append(('subject_id', 'in', course.subject_ids.ids))
        if payload.get('admission_id'):
            admission = self.env['op.admission'].browse(
                ser.require_positive_id(payload, 'admission_id')
            )
            if admission.partner_id:
                grade_domain.append(('partner_id', '=', admission.partner_id.id))
        maps = 0
        if 'irg.moodle.subject.map' in self.env:
            maps = self.env['irg.moodle.subject.map'].search_count(map_domain or [])
        grades = self.env['irg.moodle.grade'].search(grade_domain, order='last_sync desc', limit=50)
        unmatched = grades.filtered(lambda row: row.state == 'unmatched_student')
        last_sync = grades[:1].last_sync if grades else False
        return {
            'available': True,
            'maps': maps,
            'grades': len(grades),
            'unmatched': len(unmatched),
            'last_sync': last_sync,
            'unmatched_ids': unmatched.ids,
        }
