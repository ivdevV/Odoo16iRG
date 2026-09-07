from datetime import date, timedelta
from pathlib import Path
from threading import Barrier, Thread
from unittest.mock import patch
from uuid import uuid4

from psycopg2 import IntegrityError

from odoo import api
from odoo.exceptions import AccessError, ValidationError
from odoo.modules.registry import Registry
from odoo.tests.common import TransactionCase, tagged

from ..models.op_student_course import irg_parse_tfm_batch_eligibility


@tagged('post_install', '-at_install')
class TestTfmConvocatorias(TransactionCase):
    def _suffix(self):
        return uuid4().hex[:8]

    def _course_and_batch(self, code, activate_tesis=True):
        suffix = self._suffix()
        channel = self.env['slide.channel'].create({
            'name': 'TFM channel %s' % suffix,
        })
        course = self.env['op.course'].create({
            'name': 'TFM course %s' % suffix,
            'code': 'TFM-%s' % suffix,
            'lang': 'en_US',
            'activate_tesis': activate_tesis,
            'irg_tfm_channel_id': channel.id,
        })
        batch = self.env['op.batch'].create({
            'name': 'TFM batch %s' % suffix,
            'code': code,
            'course_id': course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=60),
        })
        return course, batch

    def _student_course(self, code='HC2511', progress=50, activate_tesis=True):
        course, batch = self._course_and_batch(code, activate_tesis)
        suffix = self._suffix()
        partner = self.env['res.partner'].create({
            'name': 'TFM student %s' % suffix,
            'email': 'tfm.%s@example.test' % suffix,
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'TFM',
            'last_name': suffix,
            'gender': 'o',
        })
        enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'roll_number': 'TFM-%s' % suffix,
        })
        with patch.object(
            type(enrollment),
            '_irg_tfm_completion_percentage',
            return_value=progress,
        ):
            enrollment._irg_ensure_tfm_record()
        return enrollment

    def _create_committed_activation_case(self, registry):
        """Create an eligible fixture visible to independently committed cursors."""
        suffix = self._suffix()
        with registry.cursor() as cursor:
            env = api.Environment(cursor, self.env.uid, {})
            course = env['op.course'].create({
                'name': 'Concurrent TFM course %s' % suffix,
                'code': 'CONCURRENT-TFM-%s' % suffix,
                'lang': 'en_US',
                'activate_tesis': True,
                'irg_tfm_channel_id': env['slide.channel'].create({
                    'name': 'Concurrent TFM channel %s' % suffix,
                }).id,
            })
            batch = env['op.batch'].create({
                'name': 'Concurrent TFM batch %s' % suffix,
                'code': 'HC2511',
                'course_id': course.id,
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=60),
            })
            partner = env['res.partner'].create({
                'name': 'Concurrent TFM student %s' % suffix,
                'email': 'concurrent.tfm.%s@example.test' % suffix,
            })
            student = env['op.student'].create({
                'partner_id': partner.id,
                'first_name': 'Concurrent',
                'last_name': suffix,
                'gender': 'o',
            })
            enrollment = env['op.student.course'].create({
                'student_id': student.id,
                'course_id': course.id,
                'batch_id': batch.id,
                'roll_number': 'CONCURRENT-TFM-%s' % suffix,
            })
            identifiers = {
                'course': course.id,
                'channel': course.irg_tfm_channel_id.id,
                'batch': batch.id,
                'partner': partner.id,
                'student': student.id,
                'enrollment': enrollment.id,
            }
            cursor.commit()
        return identifiers

    def _gradebook_subjects_for(self, enrollment, count=2):
        suffix = self._suffix()
        product = self.env['product.product'].create({
            'name': 'TFM academic service %s' % suffix,
            'type': 'service',
        })
        register = self.env['op.admission.register'].create({
            'name': 'TFM register %s' % suffix,
            'course_id': enrollment.course_id.id,
            'product_id': product.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=60),
            'min_count': 1,
            'max_count': 10,
        })
        admission = self.env['op.admission'].create({
            'name': enrollment.student_id.name,
            'partner_id': enrollment.student_id.partner_id.id,
            'student_id': enrollment.student_id.id,
            'course_id': enrollment.course_id.id,
            'batch_id': enrollment.batch_id.id,
            'register_id': register.id,
            'application_number': 'TFM-ADM-%s' % suffix,
            'first_name': enrollment.student_id.first_name,
            'last_name': enrollment.student_id.last_name,
            'gender': enrollment.student_id.gender,
            'email': enrollment.student_id.email,
            'is_student': True,
        })
        gradebook = self.env['app.gradebook.student'].create({
            'admission_id': admission.id,
            'state': 'in_progress',
        })
        subjects = self.env['app.gradebook.subject']
        for index in range(count):
            subject = self.env['op.subject'].create({
                'name': 'TFM subject %s %s' % (index, suffix),
                'code': 'TFM-SUB-%s-%s' % (index, suffix),
                'course_id': enrollment.course_id.id,
                'subject_type': 'compulsory',
            })
            subjects |= self.env['app.gradebook.subject'].create({
                'gradebook_student_id': gradebook.id,
                'op_subject_id': subject.id,
            })
        return subjects

    def _cleanup_committed_activation_case(self, registry, identifiers):
        with registry.cursor() as cursor:
            env = api.Environment(cursor, self.env.uid, {})
            env['tesis.model'].search([
                ('course_id', '=', identifiers['enrollment']),
            ]).unlink()
            env['op.student.course'].browse(identifiers['enrollment']).exists().unlink()
            env['op.student'].browse(identifiers['student']).exists().unlink()
            env['op.batch'].browse(identifiers['batch']).exists().unlink()
            env['op.course'].browse(identifiers['course']).exists().unlink()
            env['slide.channel'].browse(identifiers['channel']).exists().unlink()
            env['res.partner'].browse(identifiers['partner']).exists().unlink()
            cursor.commit()

    def test_batch_parser_enforces_approved_cutoffs_and_exclusions(self):
        expected = {
            'HC2509': False,
            'HC2511': ('HC', 2511),
            'MONLHC2511': False,
            'monlhc2601': ('HC', 2601),
            'ONL2601': False,
            'ONL2602': ('ONL', 2602),
            'PRS-HC2701': False,
            'other': False,
        }
        for code, result in expected.items():
            self.assertEqual(irg_parse_tfm_batch_eligibility(code), result, code)

    def test_real_completion_field_is_available_nonstored_and_read_by_service(self):
        field = self.env['op.student.course']._fields['completion_porc']
        self.assertFalse(field.store)
        enrollment = self._student_course(progress=0)
        self.assertEqual(enrollment._irg_tfm_completion_percentage(), 0.0)

    def test_exam_result_crossing_real_fifty_percent_activates_tfm(self):
        enrollment = self._student_course(progress=0)
        gradebook_subjects = self._gradebook_subjects_for(enrollment, count=2)
        self.assertEqual(enrollment._irg_tfm_completion_percentage(), 0.0)

        result = self.env['app.gradebook.result'].create({
            'gradebook_subject_id': gradebook_subjects[0].id,
            'survey_type': 'exam',
            'scoring_total': 8.0,
        })

        self.assertEqual(enrollment._irg_tfm_completion_percentage(), 50.0)
        thesis = self.env['tesis.model'].search([('course_id', '=', enrollment.id)])
        self.assertEqual(len(thesis), 1)
        result.write({'scoring_total': 7.0})
        self.assertTrue(thesis.exists(), 'activation must remain after progress regression')

    def test_eligibility_requires_exactly_fifty_percent_enabled_course_and_batch(self):
        cases = (
            (self._student_course(progress=49.99), 49.99, False),
            (self._student_course(code='PRS-HC2701'), 50, False),
            (self._student_course(code='HC2509'), 50, False),
            (self._student_course(activate_tesis=False), 50, False),
            (self._student_course(progress=50), 50, True),
        )
        for enrollment, progress, expected in cases:
            with patch.object(
                type(enrollment),
                '_irg_tfm_completion_percentage',
                return_value=progress,
            ):
                self.assertEqual(enrollment._irg_is_tfm_eligible(), expected)

    def test_eligible_enrollment_creates_one_draft_thesis_without_notification(self):
        enrollment = self._student_course(progress=49.99)
        self.assertFalse(self.env['tesis.model'].search([('course_id', '=', enrollment.id)]))

        mail_count = self.env['mail.mail'].search_count([])
        with patch.object(
            type(enrollment),
            '_irg_tfm_completion_percentage',
            return_value=50,
        ):
            enrollment.write({'roll_number': enrollment.roll_number})
        thesis = self.env['tesis.model'].search([('course_id', '=', enrollment.id)])
        self.assertEqual(len(thesis), 1)
        self.assertEqual(thesis.state, 'draft')
        self.assertEqual(thesis.name, enrollment.student_id.name)
        self.assertEqual(thesis.email, enrollment.student_id.email)
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count)

    def test_auto_activation_context_effectively_suppresses_inherited_email(self):
        enrollment = self._student_course(progress=50)
        thesis = self.env['tesis.model'].search([('course_id', '=', enrollment.id)])
        self.assertTrue(thesis.with_context(irg_tfm_auto_activation=True)._send_email_notification())

    def test_activation_is_idempotent_and_progress_regression_does_not_remove_thesis(self):
        enrollment = self._student_course(progress=50)
        thesis = enrollment._irg_ensure_tfm_record()
        self.assertEqual(thesis, enrollment._irg_ensure_tfm_record())
        with patch.object(
            type(enrollment),
            '_irg_tfm_completion_percentage',
            return_value=10,
        ):
            enrollment.write({'roll_number': enrollment.roll_number})
        self.assertTrue(self.env['tesis.model'].browse(thesis.id).exists())

    def test_postgresql_constraint_rejects_second_thesis_for_same_enrollment(self):
        enrollment = self._student_course(progress=50)
        thesis = enrollment._irg_ensure_tfm_record()
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.env['tesis.model'].with_context(irg_tfm_auto_activation=True).create({
                'name': enrollment.student_id.name,
                'email': enrollment.student_id.email,
                'course_id': enrollment.id,
                'state': 'draft',
            })
        self.assertTrue(thesis.exists())

    def test_concurrent_activation_keeps_one_thesis_and_absorbs_expected_constraint(self):
        registry = Registry(self.env.cr.dbname)
        identifiers = self._create_committed_activation_case(registry)
        errors = []
        barrier = Barrier(2)

        def activate_in_separate_transaction():
            try:
                with registry.cursor() as cursor:
                    env = api.Environment(cursor, self.env.uid, {})
                    barrier.wait(timeout=10)
                    env['op.student.course'].browse(
                        identifiers['enrollment'],
                    )._irg_ensure_tfm_record()
                    cursor.commit()
            except Exception as exc:  # surfaced below; the expected constraint is internal
                errors.append(exc)

        workers = [Thread(target=activate_in_separate_transaction) for _index in range(2)]
        try:
            with patch.object(
                type(self.env['op.student.course']),
                '_irg_tfm_completion_percentage',
                return_value=50,
            ):
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join(timeout=15)
            self.assertFalse(any(worker.is_alive() for worker in workers))
            self.assertFalse(errors)
            with registry.cursor() as cursor:
                env = api.Environment(cursor, self.env.uid, {})
                self.assertEqual(env['tesis.model'].search_count([
                    ('course_id', '=', identifiers['enrollment']),
                ]), 1)
        finally:
            self._cleanup_committed_activation_case(registry, identifiers)
            self.env.invalidate_all()

    def test_cron_is_bounded_and_eventually_covers_eligible_enrollments(self):
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param('irg_tfm_convocatorias.activation_cursor', '0')
        enrollments = [self._student_course(progress=49.99) for _index in range(3)]

        StudentCourse = self.env['op.student.course'].with_context(
            irg_tfm_cron_batch_size=1,
        )
        with patch.object(
            type(StudentCourse),
            '_irg_tfm_completion_percentage',
            return_value=50,
        ):
            StudentCourse._cron_irg_ensure_tfm_records()
            self.assertEqual(self.env['tesis.model'].search_count([
                ('course_id', 'in', enrollments.ids),
            ]), 1)
            StudentCourse._cron_irg_ensure_tfm_records()
            StudentCourse._cron_irg_ensure_tfm_records()
            self.assertEqual(self.env['tesis.model'].search_count([
                ('course_id', 'in', enrollments.ids),
            ]), 3)
            StudentCourse._cron_irg_ensure_tfm_records()
            StudentCourse._cron_irg_ensure_tfm_records()
            self.assertEqual(self.env['tesis.model'].search_count([
                ('course_id', 'in', enrollments.ids),
            ]), 3)

    def test_convocation_assignment_and_removal_are_internal_locked_and_keep_state(self):
        thesis = self._student_course(progress=50)._irg_ensure_tfm_record()
        convocation = self.env['irg.tfm.convocatoria'].create({
            'name': 'Assignment', 'code': 'ASSIGN-%s' % self._suffix(),
        })
        initial_state = thesis.state
        initial_messages = thesis.message_ids

        thesis.write({'irg_tfm_convocation_id': convocation.id})
        self.assertEqual(thesis.irg_tfm_convocation_id, convocation)
        self.assertEqual(thesis.state, initial_state)
        self.assertGreater(len(thesis.message_ids), len(initial_messages))
        self.assertTrue(any(
            'Warning: this TFM has no outline submission yet.' in (message.body or '')
            for message in thesis.message_ids
        ))

        thesis.write({'irg_tfm_convocation_id': False})
        self.assertFalse(thesis.irg_tfm_convocation_id)
        self.assertEqual(thesis.state, initial_state)
        self.assertTrue(any(
            'TFM convocation removed' in (message.body or '')
            for message in thesis.message_ids
        ))

    def test_convocation_assignment_requires_an_internal_user(self):
        thesis = self._student_course(progress=50)._irg_ensure_tfm_record()
        convocation = self.env['irg.tfm.convocatoria'].create({
            'name': 'Private', 'code': 'PRIVATE-%s' % self._suffix(),
        })
        with self.assertRaises(AccessError):
            thesis.with_user(self.env.ref('base.public_user')).write({
                'irg_tfm_convocation_id': convocation.id,
            })

    def test_convocation_assignment_revalidates_archived_configuration(self):
        thesis = self._student_course(progress=50)._irg_ensure_tfm_record()
        convocation = self.env['irg.tfm.convocatoria'].create({
            'name': 'Archived', 'code': 'ARCHIVED-%s' % self._suffix(),
        })
        self.assertTrue(convocation.active)
        self.env.cr.execute(
            'UPDATE irg_tfm_convocatoria SET active = FALSE WHERE id = %s',
            [convocation.id],
        )

        with self.assertRaisesRegex(ValidationError, 'archived'):
            thesis.write({'irg_tfm_convocation_id': convocation.id})

    def test_convocation_assignment_revalidates_course_channel(self):
        thesis = self._student_course(progress=50)._irg_ensure_tfm_record()
        convocation = self.env['irg.tfm.convocatoria'].create({
            'name': 'No channel', 'code': 'NO-CHANNEL-%s' % self._suffix(),
        })
        course = thesis.course_id.course_id
        self.assertTrue(course.irg_tfm_channel_id)
        self.env.cr.execute(
            'UPDATE op_course SET irg_tfm_channel_id = NULL WHERE id = %s',
            [course.id],
        )

        with self.assertRaisesRegex(ValidationError, 'channel'):
            thesis.write({'irg_tfm_convocation_id': convocation.id})

    def test_convocation_transition_locks_configuration_before_theses_in_id_order(self):
        source = (
            Path(__file__).resolve().parents[1] / 'models' / 'tesis_model.py'
        ).read_text(encoding='utf-8')
        transition = source[source.index('    def write(self, vals):'):]
        convocation_lock = transition.index(
            'SELECT id FROM irg_tfm_convocatoria WHERE id = %s FOR UPDATE'
        )
        course_lock = transition.index(
            'SELECT id FROM op_course WHERE id IN %s ORDER BY id FOR UPDATE'
        )
        thesis_lock = transition.index(
            'SELECT id FROM tesis_model WHERE id IN %s ORDER BY id FOR UPDATE'
        )
        reread = transition.index("current_courses.invalidate_recordset(['irg_tfm_channel_id'])")
        self.assertLess(convocation_lock, course_lock)
        self.assertLess(course_lock, thesis_lock)
        self.assertLess(thesis_lock, reread)

    def test_direct_creation_with_convocation_is_rejected_to_centralize_transition(self):
        enrollment = self._student_course(progress=49.99)
        convocation = self.env['irg.tfm.convocatoria'].create({
            'name': 'Direct', 'code': 'DIRECT-%s' % self._suffix(),
        })
        with self.assertRaises(ValidationError):
            self.env['tesis.model'].create({
                'name': enrollment.student_id.name,
                'email': enrollment.student_id.email,
                'course_id': enrollment.id,
                'irg_tfm_convocation_id': convocation.id,
            })

    def test_convocation_normalizes_code_and_rejects_invalid_windows(self):
        Convocation = self.env['irg.tfm.convocatoria']
        today = date.today()
        convocation = Convocation.create({
            'name': 'June', 'code': ' jun-26 ',
            'partial_open_date': today,
            'partial_close_date': today,
            'final_open_date': today,
            'final_close_date': today,
        })
        self.assertEqual(convocation.code, 'JUN-26')
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            Convocation.create({'name': 'Duplicate', 'code': 'jun-26'})
        with self.assertRaises(ValidationError):
            Convocation.create({
                'name': 'Invalid', 'code': 'INVALID',
                'partial_open_date': today,
                'partial_close_date': today - timedelta(days=1),
            })
