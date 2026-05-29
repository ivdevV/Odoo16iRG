# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.fields import Date
from dateutil.relativedelta import relativedelta


class TestOpBatchOnlineScheduling(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestOpBatchOnlineScheduling, cls).setUpClass()

        # Get an installed language dynamically to satisfy the course model's lang requirement
        installed_langs = cls.env['res.lang'].get_installed()
        lang_code = installed_langs[0][0] if installed_langs else 'es_ES'

        # Create subjects
        cls.subject_1 = cls.env['op.subject'].create({
            'name': 'Subject 1',
            'code': 'SUB001',
        })
        cls.subject_2 = cls.env['op.subject'].create({
            'name': 'Subject 2',
            'code': 'SUB002',
        })
        cls.subject_3 = cls.env['op.subject'].create({
            'name': 'Subject 3',
            'code': 'SUB003',
        })

        # Create course
        cls.course = cls.env['op.course'].create({
            'name': 'Test Course',
            'code': 'TEST-CRS',
            'lang': lang_code,
            'subject_ids': [(6, 0, [cls.subject_1.id, cls.subject_2.id, cls.subject_3.id])]
        })

    def test_online_batch_scheduling_30_days_gap(self):
        """Test that an online batch (code/name contains 'ONL') correctly schedules
        its subjects with a 30-day gap between them."""

        start_date = Date.to_date('2026-06-01')
        end_date = Date.to_date('2027-06-01')

        # Create online batch (code contains 'ONL')
        batch_onl = self.env['op.batch'].create({
            'name': 'Batch 2026 ONL',
            'code': 'B-2026-ONL',
            'start_date': start_date,
            'end_date': end_date,
            'course_id': self.course.id,
        })

        # Retrieve and sort scheduled subjects (by id, same as in _schedule_onl_subjects)
        subjects_to_batch = batch_onl.subject_to_batch_ids.sorted(key=lambda r: r.id)

        self.assertEqual(len(subjects_to_batch), 3, "There should be 3 subjects in the batch")

        # Check start and end dates
        self.assertEqual(subjects_to_batch[0].date_from, start_date)
        self.assertEqual(subjects_to_batch[0].date_to, end_date)

        self.assertEqual(subjects_to_batch[1].date_from, start_date + relativedelta(days=30))
        self.assertEqual(subjects_to_batch[1].date_to, end_date)

        self.assertEqual(subjects_to_batch[2].date_from, start_date + relativedelta(days=60))
        self.assertEqual(subjects_to_batch[2].date_to, end_date)

    def test_non_online_batch_no_scheduling(self):
        """Test that a non-online batch (name/code doesn't contain 'ONL') does not
        schedule the subjects automatically."""

        start_date = Date.to_date('2026-06-01')
        end_date = Date.to_date('2027-06-01')

        # Create normal batch (no 'ONL' in code or name)
        batch_normal = self.env['op.batch'].create({
            'name': 'Batch 2026 Presencial',
            'code': 'B-2026-PRES',
            'start_date': start_date,
            'end_date': end_date,
            'course_id': self.course.id,
        })

        # Retrieve subjects
        subjects_to_batch = batch_normal.subject_to_batch_ids

        # Date from/to should not be automatically set by _schedule_onl_subjects
        for line in subjects_to_batch:
            self.assertFalse(line.date_from, "Subject start date should not be scheduled for non-online batches")
            self.assertFalse(line.date_to, "Subject end date should not be scheduled for non-online batches")

    def test_online_batch_rescheduling_on_write(self):
        """Test that modifying the start_date of an online batch triggers rescheduling
        with the correct 30-day gap."""

        start_date = Date.to_date('2026-06-01')
        end_date = Date.to_date('2027-06-01')

        # Create online batch
        batch_onl = self.env['op.batch'].create({
            'name': 'Batch 2026 ONL',
            'code': 'B-2026-ONL',
            'start_date': start_date,
            'end_date': end_date,
            'course_id': self.course.id,
        })

        # Modify the start date of the batch
        new_start_date = Date.to_date('2026-07-01')
        batch_onl.write({
            'start_date': new_start_date,
        })

        subjects_to_batch = batch_onl.subject_to_batch_ids.sorted(key=lambda r: r.id)

        # Check rescheduled start and end dates
        self.assertEqual(subjects_to_batch[0].date_from, new_start_date)
        self.assertEqual(subjects_to_batch[0].date_to, end_date)

        self.assertEqual(subjects_to_batch[1].date_from, new_start_date + relativedelta(days=30))
        self.assertEqual(subjects_to_batch[1].date_to, end_date)

        self.assertEqual(subjects_to_batch[2].date_from, new_start_date + relativedelta(days=60))
        self.assertEqual(subjects_to_batch[2].date_to, end_date)
