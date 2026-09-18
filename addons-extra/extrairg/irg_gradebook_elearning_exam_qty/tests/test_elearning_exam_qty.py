# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestElearningExamQty(TransactionCase):

    def setUp(self):
        super().setUp()
        self.counter = 0
        self.template = self.env['app.gradebook'].create({
            'name': 'IRG Exam Qty Template',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })
        self.product = self.env['product.product'].create({
            'name': 'IRG Exam Qty Product',
            'type': 'service',
        })

    def _idx(self):
        self.counter += 1
        return self.counter

    def _create_survey(self, title, survey_type='exam'):
        return self.env['survey.survey'].create({
            'title': title,
            'survey_type': survey_type,
        })

    def _create_exam_slide(
            self, channel, title, batches=None, published=True,
            scheduled=None, survey=None, survey_type='exam'):
        survey = survey or self._create_survey(title, survey_type)
        values = {
            'name': title,
            'channel_id': channel.id,
            'slide_category': 'certification',
            'survey_id': survey.id,
            'is_published': published,
        }
        if batches:
            values['allowed_batch_ids'] = [(6, 0, [b.id for b in batches])]
        if scheduled:
            values['scheduled_date'] = scheduled
        return self.env['slide.slide'].create(values)

    def _create_gradebook(self, subject_count=1, batch=None, subjects=None):
        idx = self._idx()
        if batch:
            course = batch.course_id
            if not course.gradebook_id:
                course.gradebook_id = self.template.id
        else:
            course = self.env['op.course'].create({
                'name': 'IRG Exam Qty Course %s' % idx,
                'code': 'IRGEQ%03d' % idx,
                'lang': self.env.user.lang or 'en_US',
                'gradebook_id': self.template.id,
            })
            batch = self.env['op.batch'].create({
                'name': 'IRG-EQ-%s' % idx,
                'code': 'IRG-EQ-%s' % idx,
                'course_id': course.id,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            })
        partner = self.env['res.partner'].create({
            'name': 'IRG Exam Qty Student %s' % idx,
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Exam Qty %s' % idx,
            'gender': 'm',
        })
        register = self.env['op.admission.register'].create({
            'name': 'IRG Exam Qty Register %s' % idx,
            'course_id': course.id,
            'product_id': self.product.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
        })
        admission = self.env['op.admission'].create({
            'name': 'IRG Exam Qty Admission %s' % idx,
            'first_name': 'IRG',
            'last_name': 'Exam Qty %s' % idx,
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.exam.qty.%s@example.com' % idx,
            'partner_id': partner.id,
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'register_id': register.id,
        })
        gradebook = self.env['app.gradebook.student'].create({
            'admission_id': admission.id,
            'state': 'in_progress',
        })
        lines = self.env['app.gradebook.subject']
        if subjects:
            for subject in subjects:
                lines |= self.env['app.gradebook.subject'].create({
                    'gradebook_student_id': gradebook.id,
                    'op_subject_id': subject.id,
                })
        else:
            for subject_index in range(1, subject_count + 1):
                channel = self.env['slide.channel'].create({
                    'name': 'IRG EQ Channel %s-%s' % (idx, subject_index),
                    'channel_type': 'training',
                })
                subject = self.env['op.subject'].create({
                    'name': 'IRG EQ Subject %s-%s' % (idx, subject_index),
                    'code': 'IRGEQ-%s-%s' % (idx, subject_index),
                    'subject_type': 'compulsory',
                    'course_id': course.id,
                    'slide_channel_id': channel.id,
                })
                lines |= self.env['app.gradebook.subject'].create({
                    'gradebook_student_id': gradebook.id,
                    'op_subject_id': subject.id,
                })
        return gradebook, lines, batch

    def _add_exam_result(self, line, score=10.0):
        return self.env['app.gradebook.result'].create({
            'gradebook_subject_id': line.id,
            'survey_type': 'exam',
            'scoring_total': score,
        })

    def test_unrestricted_published_exam_sets_qty_one(self):
        gradebook, lines, _batch = self._create_gradebook()
        line = lines[0]
        self._create_exam_slide(line.op_subject_id.slide_channel_id, 'Exam A')
        info = line._get_gradebook_info(line)
        self.assertEqual(info['exam']['qty'], 1)
        self.assertEqual(line._irg_elearning_exam_qty(), 1)

    def test_same_gradebook_can_require_three_and_two(self):
        gradebook, lines, batch = self._create_gradebook(subject_count=2)
        line_a, line_b = lines[0], lines[1]
        for name in ('A1', 'A2', 'A3'):
            self._create_exam_slide(
                line_a.op_subject_id.slide_channel_id,
                'Exam %s' % name,
                batches=[batch],
            )
        for name in ('B1', 'B2'):
            self._create_exam_slide(
                line_b.op_subject_id.slide_channel_id,
                'Exam %s' % name,
                batches=[batch],
            )
        self.assertEqual(line_a._get_gradebook_info(line_a)['exam']['qty'], 3)
        self.assertEqual(line_b._get_gradebook_info(line_b)['exam']['qty'], 2)

    def test_old_batch_ignores_exam_restricted_to_new_batch(self):
        _gradebook_old, lines_old, _batch_old = self._create_gradebook()
        line_old = lines_old[0]
        channel = line_old.op_subject_id.slide_channel_id
        self._create_exam_slide(channel, 'Legacy Exam')
        batch_new = self.env['op.batch'].create({
            'name': 'IRG-EQ-NEW',
            'code': 'IRG-EQ-NEW',
            'course_id': line_old.course_id.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
        })
        _gradebook_new, lines_new, _batch = self._create_gradebook(
            batch=batch_new,
            subjects=[line_old.op_subject_id],
        )
        line_new = lines_new[0]
        self._create_exam_slide(channel, 'New Exam', batches=[batch_new])
        self.assertEqual(
            line_old._get_gradebook_info(line_old)['exam']['qty'], 1,
        )
        self.assertEqual(
            line_new._get_gradebook_info(line_new)['exam']['qty'], 2,
        )

    def test_scheduled_future_exam_still_counts(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        channel = line.op_subject_id.slide_channel_id
        self._create_exam_slide(channel, 'Now', batches=[batch])
        self._create_exam_slide(
            channel,
            'Later',
            batches=[batch],
            scheduled=fields.Date.today() + timedelta(days=30),
        )
        self.assertEqual(line._get_gradebook_info(line)['exam']['qty'], 2)

    def test_unpublished_assignment_and_duplicate_survey_do_not_inflate(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        channel = line.op_subject_id.slide_channel_id
        survey = self._create_survey('Shared Exam')
        self._create_exam_slide(
            channel, 'Published', batches=[batch], survey=survey,
        )
        self._create_exam_slide(
            channel, 'Duplicate', batches=[batch], survey=survey,
        )
        self._create_exam_slide(
            channel, 'Draft', batches=[batch], published=False,
        )
        self._create_exam_slide(
            channel,
            'Homework',
            batches=[batch],
            survey_type='assignment',
        )
        self.assertEqual(line._get_gradebook_info(line)['exam']['qty'], 1)

    def test_no_channel_keeps_template_qty(self):
        gradebook, lines, _batch = self._create_gradebook()
        line = lines[0]
        line.op_subject_id.slide_channel_id = False
        info = line._get_gradebook_info(line)
        self.assertEqual(info['exam']['qty'], 1)
        self.assertEqual(line._irg_elearning_exam_qty(), 0)

    def test_close_requires_detected_qty(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        channel = line.op_subject_id.slide_channel_id
        self._create_exam_slide(channel, 'E1', batches=[batch])
        self._create_exam_slide(channel, 'E2', batches=[batch])
        self._add_exam_result(line)
        with self.assertRaises(UserError):
            gradebook.state_to_done()
        self._add_exam_result(line, score=9.0)
        gradebook.state_to_done()
        self.assertEqual(gradebook.state, 'done')

    def test_done_gradebook_does_not_replace_qty(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        self._create_exam_slide(
            line.op_subject_id.slide_channel_id, 'Only', batches=[batch],
        )
        self._add_exam_result(line)
        gradebook.state_to_done()
        self._create_exam_slide(
            line.op_subject_id.slide_channel_id,
            'After Close',
            batches=[batch],
        )
        self.assertEqual(line._get_gradebook_info(line)['exam']['qty'], 1)
