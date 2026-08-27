# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase


@tagged('post_install', '-at_install', 'irg_business_api')
class TestApiReadContract(IrgBusinessApiCase):

    def test_list_academic_periods_paginates(self):
        op = self.run_op('irg_list_academic_periods', {'limit': 10, 'offset': 0})
        data = self.result_json(op)
        self.assertEqual(op.state, 'verified')
        self.assertIn('years', data)
        self.assertTrue(any(row['id'] == self.year.id for row in data['years']))
        self.assertNotIn('password', str(data).lower())

    def test_list_courses_returns_real_fields(self):
        op = self.run_op('irg_list_courses', {'limit': 50})
        data = self.result_json(op)
        ids = [row['id'] for row in data['records']]
        self.assertIn(self.course.id, ids)
        match = next(row for row in data['records'] if row['id'] == self.course.id)
        self.assertEqual(match['name'], self.course.name)
        self.assertEqual(match['code'], self.course.code)

    def test_list_courses_rejects_unknown_payload_keys(self):
        with self.assertRaises(UserError):
            self.run_op('irg_list_courses', {'limit': 10, 'sudo': True})

    def test_get_course_overview(self):
        op = self.run_op('irg_get_course_overview', {'course_id': self.course.id})
        data = self.result_json(op)
        self.assertEqual(data['id'], self.course.id)
        self.assertIn('modalities', data)
        self.assertIn('convocatorias', data)

    def test_get_course_batches(self):
        op = self.run_op('irg_get_course_batches', {'course_id': self.course.id})
        data = self.result_json(op)
        self.assertTrue(any(row['id'] == self.batch.id for row in data['records']))
        batch = next(row for row in data['records'] if row['id'] == self.batch.id)
        self.assertEqual(batch['code'], self.batch.code)
        self.assertIn('subjects', batch)

    def test_list_subjects_includes_precedence(self):
        op = self.run_op('irg_list_subjects', {'course_id': self.course.id})
        data = self.result_json(op)
        child = next(row for row in data['records'] if row['id'] == self.subject_b.id)
        self.assertEqual(child['parent_subject_id'], self.subject.id)

    def test_get_course_structure(self):
        op = self.run_op('irg_get_course_structure', {'channel_id': self.channel.id})
        data = self.result_json(op)
        self.assertTrue(any(s['id'] == self.section.id for s in data['sections']))
        self.assertTrue(any(s['id'] == self.draft_slide.id for s in data['slides']))
        draft = next(s for s in data['slides'] if s['id'] == self.draft_slide.id)
        self.assertFalse(draft['is_published'])

    def test_get_slide(self):
        op = self.run_op('irg_get_slide', {'slide_id': self.draft_slide.id})
        data = self.result_json(op)
        self.assertEqual(data['id'], self.draft_slide.id)
        self.assertEqual(data['channel_id'], self.channel.id)
        self.assertNotIn('datas', data)

    def test_get_admission_overview(self):
        op = self.run_op('irg_get_admission_overview', {'admission_id': self.admission.id})
        data = self.result_json(op)
        self.assertEqual(data['id'], self.admission.id)
        self.assertEqual(data['course_id'], self.course.id)
        self.assertEqual(data['batch_id'], self.batch.id)
        self.assertEqual(data['state'], 'done')
        self.assertEqual(data['email'], 'api.student@example.com')

    def test_get_admission_subject_openings(self):
        op = self.run_op('irg_get_admission_subject_openings', {
            'admission_id': self.admission.id,
        })
        data = self.result_json(op)
        self.assertIn('records', data)

    def test_get_student_access(self):
        op = self.run_op('irg_get_student_access', {'admission_id': self.admission.id})
        data = self.result_json(op)
        self.assertTrue(any(row['id'] == self.membership.id for row in data['records']))
        row = next(r for r in data['records'] if r['id'] == self.membership.id)
        self.assertEqual(row['channel_id'], self.channel.id)
        self.assertEqual(row['batch_id'], self.batch.id)

    def test_get_student_academic_360(self):
        op = self.run_op('irg_get_student_academic_360', {
            'admission_id': self.admission.id,
        })
        data = self.result_json(op)
        self.assertEqual(data['admission_id'], self.admission.id)
        self.assertIn('access_count', data)
        self.assertIn('gradebook', data)
        self.assertIn('moodle', data)

    def test_get_gradebook_summary_optional(self):
        op = self.run_op('irg_get_gradebook_summary', {
            'admission_id': self.admission.id,
        })
        data = self.result_json(op)
        self.assertIn('available', data)
        if data['available']:
            self.assertIn('results', data)

    def test_get_moodle_sync_status_hides_secrets(self):
        op = self.run_op('irg_get_moodle_sync_status', {
            'course_id': self.course.id,
        })
        data = self.result_json(op)
        blob = json_lower(data)
        self.assertNotIn('token', blob)
        self.assertNotIn('password', blob)
        self.assertNotIn('wstoken', blob)

    def test_get_survey_structure_requires_id(self):
        with self.assertRaises(UserError):
            self.run_op('irg_get_survey_structure', {})

    def test_get_academic_incidents(self):
        op = self.run_op('irg_get_academic_incidents', {
            'admission_id': self.admission.id,
        })
        data = self.result_json(op)
        self.assertIn('records', data)

    def test_missing_target_id(self):
        with self.assertRaises(UserError):
            self.run_op('irg_get_slide', {'slide_id': 99999999})

    def test_page_size_cap(self):
        with self.assertRaises(UserError):
            self.run_op('irg_list_courses', {'limit': 500})

    def test_production_environment_rejected(self):
        with self.assertRaises(UserError):
            self.api_env().create({
                'operation_code': 'irg_list_courses',
                'environment': 'production',
                'request_payload': '{}',
                'idempotency_key': 'prod-1',
            })


def json_lower(data):
    import json
    return json.dumps(data).lower()
