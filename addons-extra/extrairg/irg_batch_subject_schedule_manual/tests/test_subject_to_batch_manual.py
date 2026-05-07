from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSubjectToBatchManual(TransactionCase):
    def setUp(self):
        super().setUp()
        self.SubjectToBatch = self.env['op.subject.to.batch']

        self.subject_a = self.env['op.subject'].create({
            'name': 'Manual Batch Subject A',
            'code': 'IRG-SUBJ-A',
        })
        self.subject_b = self.env['op.subject'].create({
            'name': 'Manual Batch Subject B',
            'code': 'IRG-SUBJ-B',
        })
        self.subject_outside = self.env['op.subject'].create({
            'name': 'Manual Batch Subject Outside',
            'code': 'IRG-SUBJ-OUT',
        })
        self.course = self.env['op.course'].create({
            'name': 'Manual Batch Course',
            'code': 'IRG-MBC',
            'subject_ids': [(6, 0, [self.subject_a.id, self.subject_b.id])],
        })
        self.batch = self.env['op.batch'].create({
            'name': 'IRG Manual Batch',
            'code': 'IRG-MB',
            'course_id': self.course.id,
            'start_date': date(2026, 5, 1),
            'end_date': date(2026, 12, 31),
        })
        self.batch.subject_to_batch_ids.unlink()

    def test_create_sets_subject_code_and_keeps_dates(self):
        line = self.SubjectToBatch.create({
            'batch_id': self.batch.id,
            'subject_id': self.subject_a.id,
            'date_from': date(2026, 5, 15),
            'date_to': date(2026, 6, 15),
        })

        self.assertEqual(line.code, self.subject_a.code)
        self.assertEqual(line.date_from, date(2026, 5, 15))
        self.assertEqual(line.date_to, date(2026, 6, 15))

    def test_write_subject_updates_code(self):
        line = self.SubjectToBatch.create({
            'batch_id': self.batch.id,
            'subject_id': self.subject_a.id,
        })

        line.write({'subject_id': self.subject_b.id})

        self.assertEqual(line.code, self.subject_b.code)

    def test_subject_must_belong_to_batch_course(self):
        with self.assertRaises(ValidationError):
            self.SubjectToBatch.create({
                'batch_id': self.batch.id,
                'subject_id': self.subject_outside.id,
            })

    def test_subject_cannot_be_duplicated_in_batch(self):
        self.SubjectToBatch.create({
            'batch_id': self.batch.id,
            'subject_id': self.subject_a.id,
        })

        with self.assertRaises(ValidationError):
            self.SubjectToBatch.create({
                'batch_id': self.batch.id,
                'subject_id': self.subject_a.id,
            })

    def test_batch_course_change_keeps_base_subject_autoload(self):
        new_course = self.env['op.course'].create({
            'name': 'Manual Batch New Course',
            'code': 'IRG-MBNC',
            'subject_ids': [(6, 0, [self.subject_outside.id])],
        })

        self.batch.write({'course_id': new_course.id})

        self.assertEqual(self.batch.course_id, new_course)
        self.assertEqual(self.batch.subject_to_batch_ids.subject_id, self.subject_outside)