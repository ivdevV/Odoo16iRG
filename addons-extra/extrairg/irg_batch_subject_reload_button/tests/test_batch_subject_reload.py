from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBatchSubjectReload(TransactionCase):
    def setUp(self):
        super().setUp()
        self.SubjectToBatch = self.env['op.subject.to.batch']
        self.subject_a = self.env['op.subject'].create({
            'name': 'Reload Subject A',
            'code': 'IRG-RSA',
        })
        self.subject_b = self.env['op.subject'].create({
            'name': 'Reload Subject B',
            'code': 'IRG-RSB',
        })
        self.subject_c = self.env['op.subject'].create({
            'name': 'Reload Subject C',
            'code': 'IRG-RSC',
        })
        self.subject_outside = self.env['op.subject'].create({
            'name': 'Reload Subject Outside',
            'code': 'IRG-RSO',
        })
        self.course = self.env['op.course'].create({
            'name': 'Reload Course',
            'code': 'IRG-RC',
            'subject_ids': [(6, 0, [
                self.subject_a.id,
                self.subject_b.id,
                self.subject_c.id,
            ])],
        })
        self.batch = self.env['op.batch'].create({
            'name': 'IRG Reload Batch',
            'code': 'IRG-RB',
            'course_id': self.course.id,
            'start_date': date(2026, 5, 1),
            'end_date': date(2026, 12, 31),
        })
        self.batch.subject_to_batch_ids.unlink()

    def test_reload_adds_missing_subjects(self):
        self.batch.action_irg_reload_subject_to_batch()
        self.batch.invalidate_recordset(['subject_to_batch_ids'])

        self.assertEqual(
            set(self.batch.subject_to_batch_ids.mapped('subject_id').ids),
            {self.subject_a.id, self.subject_b.id, self.subject_c.id},
        )

    def test_reload_preserves_existing_dates(self):
        line = self.SubjectToBatch.create({
            'batch_id': self.batch.id,
            'subject_id': self.subject_a.id,
            'date_from': date(2026, 6, 1),
            'date_to': date(2026, 7, 1),
        })

        self.batch.action_irg_reload_subject_to_batch()
        self.batch.invalidate_recordset(['subject_to_batch_ids'])

        self.assertTrue(line.exists())
        self.assertEqual(line.date_from, date(2026, 6, 1))
        self.assertEqual(line.date_to, date(2026, 7, 1))

    def test_reload_removes_outside_and_duplicate_lines(self):
        self.SubjectToBatch.create({
            'batch_id': self.batch.id,
            'subject_id': self.subject_a.id,
        })
        self.SubjectToBatch.with_context(irg_skip_subject_course_check=True).create({
            'batch_id': self.batch.id,
            'subject_id': self.subject_outside.id,
        })

        self.batch.action_irg_reload_subject_to_batch()
        self.batch.invalidate_recordset(['subject_to_batch_ids'])

        self.assertEqual(
            len(self.batch.subject_to_batch_ids.filtered(
                lambda line: line.subject_id == self.subject_a
            )),
            1,
        )
        self.assertNotIn(
            self.subject_outside,
            self.batch.subject_to_batch_ids.mapped('subject_id'),
        )

    def test_reload_requires_course(self):
        batch_without_course = self.env['op.batch'].new({
            'name': 'IRG Reload Batch Without Course',
            'code': 'IRG-RBWC',
            'start_date': date(2026, 5, 1),
            'end_date': date(2026, 12, 31),
        })

        with self.assertRaises(UserError):
            batch_without_course.action_irg_reload_subject_to_batch()