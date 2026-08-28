# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tools.translate import _

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

    def describe_moodle_course_mapping(self, payload):
        if 'irg.moodle.subject.map' not in self.env:
            raise UserError(_('Moodle subject maps are not installed.'))
        maps = payload.get('maps') or []
        if not isinstance(maps, list) or not maps:
            raise UserError(_('maps must be a non-empty list.'))
        proposed = []
        for row in maps:
            if not isinstance(row, dict):
                raise UserError(_('Each map must be an object.'))
            moodle_course_id = ser.require_positive_id(row, 'moodle_course_id')
            subject_id = ser.require_positive_id(row, 'subject_id')
            subject = self.env['op.subject'].browse(subject_id)
            if not subject.exists():
                raise UserError(_('Unknown subject id %s.') % subject_id)
            proposed.append({
                'moodle_course_id': moodle_course_id,
                'subject_id': subject.id,
                'course_id': row.get('course_id') or (subject.course_id.id if 'course_id' in subject._fields and subject.course_id else False),
            })
        return {'maps': proposed, 'import_catalogue': False}

    def preview_apply_moodle_course_mapping(self, payload):
        plan = self.describe_moodle_course_mapping(payload)
        return {'maps': []}, plan, {'model': 'irg.moodle.subject.map', 'id': False}

    def apply_moodle_course_mapping(self, proposed, before):
        Map = self.env['irg.moodle.subject.map']
        ids = []
        for row in proposed.get('maps') or []:
            existing = Map.with_context(active_test=False).search(
                [('moodle_course_id', '=', row['moodle_course_id'])], limit=1,
            )
            vals = {
                'subject_id': row['subject_id'],
                'moodle_course_id': row['moodle_course_id'],
            }
            if row.get('course_id') and 'course_id' in Map._fields:
                vals['course_id'] = row['course_id']
            if existing:
                existing.write(vals)
                ids.append(existing.id)
            else:
                ids.append(Map.create(vals).id)
        return {'map_ids': ids}

    def describe_moodle_grade_sync(self, payload):
        status = self.get_moodle_sync_status(payload)
        status['will_call'] = '_sync_moodle_grades'
        status['returns_tokens'] = False
        return status

    def preview_apply_moodle_grade_sync(self, payload):
        plan = self.describe_moodle_grade_sync(payload)
        return plan, dict(plan), {'model': 'irg.moodle.grade', 'id': False}

    def apply_moodle_grade_sync(self, proposed, before):
        if 'irg.moodle.grade' not in self.env:
            raise UserError(_('Moodle grades are not installed.'))
        Grade = self.env['irg.moodle.grade']
        if not hasattr(Grade, '_sync_moodle_grades'):
            raise UserError(_('Official Moodle grade sync is not available.'))
        counters = Grade._sync_moodle_grades()
        return {
            'courses': counters.get('courses', 0),
            'synced': counters.get('synced', 0),
            'unmatched': counters.get('unmatched', 0),
            'skipped': counters.get('skipped', 0),
        }

    def preview_confirm_moodle_student_match(self, payload):
        if 'irg.moodle.grade' not in self.env:
            raise UserError(_('Moodle grades are not installed.'))
        grade = self.env['irg.moodle.grade'].browse(ser.require_positive_id(payload, 'grade_id'))
        if not grade.exists():
            raise UserError(_('Unknown Moodle grade id.'))
        student = self.env['op.student'].browse(ser.require_positive_id(payload, 'student_id'))
        if not student.exists():
            raise UserError(_('Unknown student id.'))
        before = {
            'id': grade.id,
            'state': grade.state,
            'student_id': grade.student_id.id if grade.student_id else False,
        }
        proposed = {
            'id': grade.id,
            'student_id': student.id,
            'state': 'synced',
            'match_method': 'manual',
        }
        return before, proposed, {'model': 'irg.moodle.grade', 'id': grade.id}

    def apply_confirm_moodle_student_match(self, proposed, before):
        grade = self.env['irg.moodle.grade'].browse(proposed['id'])
        if grade.state != before.get('state'):
            raise UserError(_('The Moodle grade changed after preview.'))
        vals = {
            'student_id': proposed['student_id'],
            'state': 'synced',
        }
        if 'match_method' in grade._fields:
            vals['match_method'] = 'manual'
        grade.write(vals)
        return {
            'id': grade.id,
            'student_id': grade.student_id.id,
            'state': grade.state,
        }
