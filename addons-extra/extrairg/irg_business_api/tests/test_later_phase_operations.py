# -*- coding: utf-8 -*-
import base64

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase


@tagged('post_install', '-at_install', 'irg_business_api')
class TestLaterPhaseOperations(IrgBusinessApiCase):

    def test_preview_withdrawal_does_not_call_action_down(self):
        state = self.admission.state
        op = self.run_op('irg_preview_withdrawal', {'admission_id': self.admission.id})
        plan = self.result_json(op)
        self.assertTrue(plan['refused'])
        self.assertFalse(plan['would_call_action_down'])
        self.admission.invalidate_recordset()
        self.assertEqual(self.admission.state, state)

    def test_apply_withdrawal_is_refused(self):
        state = self.admission.state
        op = self.run_op('irg_apply_withdrawal', {'admission_id': self.admission.id}, key='wd-1')
        with self.assertRaises(UserError):
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='wd-1-ok')
        self.admission.invalidate_recordset()
        self.assertEqual(self.admission.state, state)

    def test_apply_enrollment_refuses_already_done(self):
        op = self.run_op('irg_apply_enrollment', {'admission_id': self.admission.id}, key='enr-1')
        with self.assertRaises(UserError):
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='enr-1-ok')

    def test_subject_opening_and_access_preview(self):
        openings = self.run_op('irg_preview_subject_opening', {
            'admission_id': self.admission.id,
        })
        self.assertIn('opening_count', self.result_json(openings))
        access = self.run_op('irg_preview_access_reconciliation', {
            'admission_id': self.admission.id,
        })
        self.assertGreaterEqual(self.result_json(access)['membership_count'], 1)

    def test_apply_subject_opening(self):
        op = self.run_op('irg_apply_subject_opening', {
            'admission_id': self.admission.id,
        }, key='open-1')
        self.run_op('irg_approve_operation', {'operation_id': op.id}, key='open-1-ok')
        op.invalidate_recordset()
        self.assertEqual(op.state, 'verified')

    def test_batch_schedule_roundtrip(self):
        if 'op.subject.to.batch' not in self.env:
            return
        self.env['op.subject.to.batch'].create({
            'batch_id': self.batch.id,
            'subject_id': self.subject.id,
        })
        read_op = self.run_op('irg_get_batch_schedule', {'batch_id': self.batch.id})
        self.assertTrue(self.result_json(read_op)['records'])
        write_op = self.run_op('irg_apply_batch_schedule_sync', {
            'batch_id': self.batch.id,
            'lines': [{
                'subject_id': self.subject.id,
                'date_from': '2026-02-01',
                'date_to': '2026-02-28',
            }],
        }, key='sched-1')
        self.run_op('irg_approve_operation', {'operation_id': write_op.id}, key='sched-1-ok')
        line = self.env['op.subject.to.batch'].search([
            ('batch_id', '=', self.batch.id),
            ('subject_id', '=', self.subject.id),
        ], limit=1)
        if 'date_from' in line._fields:
            self.assertEqual(str(line.date_from), '2026-02-01')

    def test_eligibility_read(self):
        op = self.run_op('irg_get_student_subject_eligibility', {
            'subject_id': self.subject.id,
            'admission_id': self.admission.id,
        })
        self.assertIn('can_be_taken', self.result_json(op))

    def test_create_survey_draft(self):
        if 'survey.survey' not in self.env:
            return
        op = self.run_op('irg_create_survey_draft', {'title': 'API draft exam'}, key='surv-1')
        self.run_op('irg_approve_operation', {'operation_id': op.id}, key='surv-1-ok')
        op.invalidate_recordset()
        survey = self.env['survey.survey'].browse(self.result_json(op)['id'])
        self.assertEqual(survey.title, 'API draft exam')

    def test_upload_private_attachment(self):
        payload = {
            'res_model': 'slide.slide',
            'res_id': self.draft_slide.id,
            'name': 'note.txt',
            'mimetype': 'text/plain',
            'file_b64': base64.b64encode(b'hello api').decode('ascii'),
        }
        op = self.run_op('irg_upload_private_attachment', payload, key='att-1')
        self.run_op('irg_approve_operation', {'operation_id': op.id}, key='att-1-ok')
        op.invalidate_recordset()
        attachment = self.env['ir.attachment'].browse(self.result_json(op)['id'])
        self.assertEqual(attachment.name, 'note.txt')
        if 'public' in attachment._fields:
            self.assertFalse(attachment.public)

    def test_attachment_metadata_hides_payload(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'meta.txt',
            'res_model': 'slide.slide',
            'res_id': self.draft_slide.id,
            'datas': base64.b64encode(b'secret-bytes'),
        })
        op = self.run_op('irg_get_attachment_metadata', {'attachment_id': attachment.id})
        data = self.result_json(op)
        self.assertEqual(data['name'], 'meta.txt')
        self.assertNotIn('datas', data)
        self.assertNotIn('raw', data)
