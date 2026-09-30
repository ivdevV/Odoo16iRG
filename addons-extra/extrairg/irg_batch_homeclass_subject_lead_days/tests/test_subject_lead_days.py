# -*- coding: utf-8 -*-
from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.irg_batch_homeclass_api_scheduler.models.op_batch import (
    OpBatch as SchedulerOpBatch,
)
from odoo.addons.irg_batch_homeclass_subject_lead_days.models.op_batch import (
    IRG_HOMECLASS_SUBJECT_LEAD_DAYS,
)


@tagged('post_install', '-at_install')
class TestHomeclassSubjectLeadDays(TransactionCase):

    def setUp(self):
        super().setUp()
        requests_patcher = patch(
            'odoo.addons.irg_batch_homeclass_api_scheduler.models.op_batch.requests.get',
            side_effect=AssertionError('Calendar API must not be called in these tests'),
        )
        requests_patcher.start()
        self.addCleanup(requests_patcher.stop)

        self.subject_matched = self.env['op.subject'].create({
            'name': 'IRG Lead Days Matched',
            'code': 'IRG-HCSLD-A',
        })
        self.subject_fallback = self.env['op.subject'].create({
            'name': 'IRG Lead Days Fallback',
            'code': 'IRG-HCSLD-B',
        })
        self.course = self.env['op.course'].create({
            'name': 'IRG Lead Days Course',
            'code': 'IRG-HCSLD-C',
            'lang': self.env.user.lang or 'en_US',
            'subject_ids': [(6, 0, [
                self.subject_matched.id,
                self.subject_fallback.id,
            ])],
        })
        self.modality_hc = self.env['op.modality'].search(
            [('code', '=', 'HC')], limit=1
        )
        if not self.modality_hc:
            self.modality_hc = self.env['op.modality'].create({
                'name': 'HomeClass',
                'code': 'HC',
                'new_code': 'HC',
                'analytic_code': 'HC',
            })
        self.batch = self.env['op.batch'].with_context(
            skip_homeclass_sync=True,
        ).create({
            'name': 'IRG-HCSLD-HC01',
            'code': 'IRG-HCSLD-HC01',
            'course_id': self.course.id,
            'modality_id': self.modality_hc.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
            'date_start_class': date(2026, 2, 1),
        })
        self.assertTrue(self.batch.is_homeclass_batch)
        self.assertEqual(len(self.batch.subject_to_batch_ids), 2)

    def _line(self, subject):
        return self.batch.subject_to_batch_ids.filtered(
            lambda line: line.subject_id == subject
        )

    def _fake_parent_success(self, batch):
        batch.ensure_one()
        matched = batch.subject_to_batch_ids.filtered(
            lambda line: line.subject_id.code == 'IRG-HCSLD-A'
        )
        fallback = batch.subject_to_batch_ids - matched
        matched.write({
            'date_from': date(2026, 1, 16),
            'date_to': batch.end_date,
        })
        fallback.write({
            'date_from': batch.start_date,
            'date_to': batch.end_date,
        })
        batch.write({'date_start_class': date(2026, 1, 16)})
        return True

    def test_apply_shifts_date_from_only(self):
        self.batch.with_context(skip_homeclass_sync=True).write({
            'date_start_class': date(2026, 1, 16),
        })
        self._line(self.subject_matched).write({
            'date_from': date(2026, 1, 16),
            'date_to': date(2026, 12, 31),
        })
        self._line(self.subject_fallback).write({
            'date_from': date(2026, 1, 1),
            'date_to': date(2026, 12, 31),
        })

        self.batch._irg_apply_homeclass_subject_lead_days()

        self.assertEqual(IRG_HOMECLASS_SUBJECT_LEAD_DAYS, 3)
        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 1, 13),
        )
        self.assertEqual(
            self._line(self.subject_fallback).date_from,
            date(2025, 12, 29),
        )
        self.assertEqual(
            self._line(self.subject_matched).date_to,
            date(2026, 12, 31),
        )
        self.assertEqual(
            self._line(self.subject_fallback).date_to,
            date(2026, 12, 31),
        )
        self.assertEqual(self.batch.date_start_class, date(2026, 1, 16))

    def test_apply_skips_empty_date_from(self):
        line = self._line(self.subject_matched)
        line.write({'date_from': False, 'date_to': date(2026, 12, 31)})
        self.batch._irg_apply_homeclass_subject_lead_days()
        self.assertFalse(line.date_from)
        self.assertEqual(line.date_to, date(2026, 12, 31))

    def test_sync_success_shifts_and_keeps_class_start(self):
        with patch.object(
            SchedulerOpBatch,
            '_sync_homeclass_calendar',
            autospec=True,
            side_effect=self._fake_parent_success,
        ):
            result = self.batch._sync_homeclass_calendar()

        self.assertTrue(result)
        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 1, 13),
        )
        self.assertEqual(
            self._line(self.subject_fallback).date_from,
            date(2025, 12, 29),
        )
        self.assertEqual(
            self._line(self.subject_matched).date_to,
            date(2026, 12, 31),
        )
        self.assertEqual(self.batch.date_start_class, date(2026, 1, 16))

    def test_sync_failure_leaves_dates_untouched(self):
        self._line(self.subject_matched).write({
            'date_from': date(2026, 6, 1),
            'date_to': date(2026, 6, 30),
        })
        with patch.object(
            SchedulerOpBatch,
            '_sync_homeclass_calendar',
            autospec=True,
            return_value=False,
        ):
            result = self.batch._sync_homeclass_calendar()

        self.assertFalse(result)
        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 6, 1),
        )
        self.assertEqual(
            self._line(self.subject_matched).date_to,
            date(2026, 6, 30),
        )
        self.assertEqual(self.batch.date_start_class, date(2026, 2, 1))

    def test_sync_is_idempotent_against_parent_absolute_dates(self):
        with patch.object(
            SchedulerOpBatch,
            '_sync_homeclass_calendar',
            autospec=True,
            side_effect=self._fake_parent_success,
        ):
            self.batch._sync_homeclass_calendar()
            self.batch._sync_homeclass_calendar()

        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 1, 13),
        )
