from contextlib import ExitStack
from datetime import date, timedelta
from unittest.mock import patch
from uuid import uuid4

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged


SUBJECT_ERROR = 'Debe existir una única asignatura del curso vinculada al Canal TFM.'
GRADEBOOK_ERROR = 'No se encontró una única libreta para el alumno, curso y lote.'
LINE_ERROR = 'La libreta no contiene una única línea para la asignatura TFM.'
EXAM_ERROR = (
    'La asignatura TFM contiene varios exámenes sin vínculo; solicite una '
    'corrección autorizada de la configuración antes de continuar.'
)
NORMALIZATION_ERROR = (
    'La escala, precisión o límites de la libreta transformarían la nota TFM; '
    'corrija la plantilla para conservar exactamente la calificación solicitada.'
)
CONCURRENT_MAPPING_ERROR = (
    'La configuración TFM cambió durante la operación; vuelva a intentarlo.'
)
LINKED_EXAM_ERROR = (
    'La asignatura TFM ya tiene su calificación vinculada al expediente; '
    'edite ese resultado en lugar de crear otro examen.'
)
LINKED_IDENTITY_ERROR = (
    'No se puede modificar ni eliminar la identidad de una calificación TFM '
    'vinculada; solicite una corrección autorizada de la configuración.'
)
IDENTITY_CONVOCATION_ERROR = (
    'Cambie la matrícula y la convocatoria TFM en operaciones separadas.'
)
MIXED_RESULT_ERROR = (
    'No se puede sincronizar un conjunto mixto de resultados TFM y no TFM; '
    'edítelos por separado.'
)


@tagged('post_install', '-at_install')
class TestTfmGradebookSync(TransactionCase):
    """Runtime contracts for deterministic, server-owned forward grade sync."""

    def setUp(self):
        super().setUp()
        suffix = self._suffix()
        self.reviewer = new_test_user(
            self.env,
            login='tfm.reviewer.%s@example.test' % suffix,
            groups='irg_tfm_convocatorias.group_tfm_reviewer',
            name='TFM Reviewer %s' % suffix,
        )
        self.internal_user = new_test_user(
            self.env,
            login='tfm.internal.%s@example.test' % suffix,
            groups='base.group_user',
            name='TFM Internal %s' % suffix,
        )
        self.portal_user = new_test_user(
            self.env,
            login='tfm.portal.%s@example.test' % suffix,
            groups='base.group_portal',
            name='TFM Portal %s' % suffix,
        )
        self.gradebook_user = new_test_user(
            self.env,
            login='tfm.gradebook.%s@example.test' % suffix,
            groups='base.group_user,isep_gradebook.isep_gradebook_admin',
            name='TFM Gradebook %s' % suffix,
        )
        case = self._build_case()
        for name, value in case.items():
            setattr(self, name, value)

    def _suffix(self):
        return uuid4().hex[:8]

    def _build_case(self, modality='HC', create_thesis=True):
        suffix = self._suffix()
        home_channel = self.env['slide.channel'].create({
            'name': 'TFM HomeClass %s' % suffix,
        })
        online_channel = self.env['slide.channel'].create({
            'name': 'TFM Online %s' % suffix,
            'irg_homeclass_channel_id': home_channel.id,
        })
        home_channel.irg_online_channel_id = online_channel
        template = self.env['app.gradebook'].create({
            'name': 'TFM exact gradebook %s' % suffix,
            'grading_scale': 10.0,
            'round_subject_result': False,
            'round_subject_avg': False,
            'round_subject_final': False,
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })
        course = self.env['op.course'].create({
            'name': 'TFM grade sync course %s' % suffix,
            'code': 'TFM-GRADE-%s' % suffix,
            'lang': 'en_US',
            'activate_tesis': True,
            'irg_tfm_channel_id': home_channel.id,
            'gradebook_id': template.id,
        })
        batch = self.env['op.batch'].create({
            'name': 'TFM grade sync batch %s' % suffix,
            'code': 'ONL2602' if modality == 'ONL' else 'HC2511',
            'course_id': course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=60),
        })
        subject = self.env['op.subject'].create({
            'name': 'TFM grade sync subject %s' % suffix,
            'code': 'TFM-GRADE-SUB-%s' % suffix,
            'course_id': course.id,
            'subject_type': 'compulsory',
            'slide_channel_id': (
                online_channel.id if modality == 'ONL' else home_channel.id
            ),
            'gradebook_id': template.id,
        })
        course.write({'subject_ids': [(4, subject.id)]})
        partner = self.env['res.partner'].create({
            'name': 'TFM grade sync student %s' % suffix,
            'email': 'tfm.grade.student.%s@example.test' % suffix,
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'TFM Grade',
            'last_name': suffix,
            'gender': 'o',
        })
        enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'roll_number': 'TFM-GRADE-%s' % suffix,
        })
        product = self.env['product.product'].create({
            'name': 'TFM grade sync service %s' % suffix,
            'type': 'service',
        })
        register = self.env['op.admission.register'].create({
            'name': 'TFM grade sync register %s' % suffix,
            'course_id': course.id,
            'product_id': product.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=60),
            'min_count': 1,
            'max_count': 10,
        })
        admission = self.env['op.admission'].create({
            'name': student.name,
            'partner_id': partner.id,
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'register_id': register.id,
            'application_number': 'TFM-GRADE-ADM-%s' % suffix,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'gender': student.gender,
            'email': student.email,
            'is_student': True,
        })
        gradebook = self.env['app.gradebook.student'].create({
            'admission_id': admission.id,
            'state': 'in_progress',
        })
        gradebook_subject = self.env['app.gradebook.subject'].create({
            'gradebook_student_id': gradebook.id,
            'op_subject_id': subject.id,
        })
        thesis = self.env['tesis.model']
        if create_thesis:
            thesis = self.env['tesis.model'].with_context(
                irg_tfm_auto_activation=True,
            ).create(self._thesis_values(enrollment))
        return {
            'home_channel': home_channel,
            'online_channel': online_channel,
            'template': template,
            'course': course,
            'batch': batch,
            'subject': subject,
            'partner': partner,
            'student': student,
            'enrollment': enrollment,
            'admission': admission,
            'gradebook': gradebook,
            'gradebook_subject': gradebook_subject,
            'thesis': thesis,
        }

    def _thesis_values(self, enrollment, **extra):
        values = {
            'name': enrollment.student_id.name,
            'email': enrollment.student_id.email,
            'course_id': enrollment.id,
            'state': 'draft',
            'irg_tfm_activated_at': fields.Datetime.now(),
        }
        values.update(extra)
        return values

    def _linked_results(self, thesis=None):
        thesis = thesis or self.thesis
        return self.env['app.gradebook.result'].sudo().search([
            ('irg_tfm_thesis_id', '=', thesis.id),
        ])

    def _audit_messages(self, thesis=None):
        thesis = thesis or self.thesis
        return thesis.sudo().message_ids.filtered(
            lambda message: 'Sincronización de nota TFM:' in (message.body or '')
        )

    def _create_exam(self, score=7.0):
        """A historical exam row that predates the TFM link.

        The public boundary now links and mirrors any exam it creates on the TFM
        line, so an unlinked legacy row is built through the super-scoped
        business helper, exactly like the rows an upgrade leaves untouched.
        """
        return self.env['app.gradebook.result'].sudo()._irg_tfm_create_business({
            'gradebook_subject_id': self.gradebook_subject.id,
            'survey_type': 'exam',
            'scoring_total': score,
        })

    def _ordinary_subject(self):
        """A course subject deliberately outside the configured Canal TFM family."""
        suffix = self._suffix()
        channel = self.env['slide.channel'].create({
            'name': 'Ordinary channel %s' % suffix,
        })
        subject = self.env['op.subject'].create({
            'name': 'Ordinary subject %s' % suffix,
            'code': 'TFM-ORD-%s' % suffix,
            'course_id': self.course.id,
            'subject_type': 'compulsory',
            'slide_channel_id': channel.id,
            'gradebook_id': self.template.id,
        })
        self.course.write({'subject_ids': [(4, subject.id)]})
        return subject

    def _ordinary_line(self):
        return self.env['app.gradebook.subject'].create({
            'gradebook_student_id': self.gradebook.id,
            'op_subject_id': self._ordinary_subject().id,
        })

    def _sync_counters(self):
        """Count both private coordinators to prove one hop, never recursion."""
        counters = {'forward': 0, 'reverse': 0}
        thesis_class = type(self.env['tesis.model'])
        forward = thesis_class._irg_tfm_sync_points_to_gradebook
        reverse = thesis_class._irg_tfm_sync_gradebook_to_points

        def counted_forward(records, *args, **kwargs):
            counters['forward'] += 1
            return forward(records, *args, **kwargs)

        def counted_reverse(records, *args, **kwargs):
            counters['reverse'] += 1
            return reverse(records, *args, **kwargs)

        patchers = (
            patch.object(
                thesis_class,
                '_irg_tfm_sync_points_to_gradebook',
                counted_forward,
            ),
            patch.object(
                thesis_class,
                '_irg_tfm_sync_gradebook_to_points',
                counted_reverse,
            ),
        )
        return counters, patchers

    def _reverse_state(self, results=None, thesis=None):
        thesis = thesis if thesis is not None else self.thesis
        results = results if results is not None else self._linked_results()
        thesis.invalidate_recordset(['points_fin'])
        return {
            'points': thesis.points_fin,
            'result_ids': results.ids,
            'scores': results.mapped('scoring_total'),
            'links': results.mapped('irg_tfm_thesis_id').ids,
            'count': self.env['app.gradebook.result'].sudo().search_count([
                ('gradebook_subject_id', '=', self.gradebook_subject.id),
            ]),
            'messages': self._audit_messages(thesis).ids,
        }

    def _assert_reverse_state_unchanged(self, before, results=None, thesis=None):
        thesis = thesis if thesis is not None else self.thesis
        results = results if results is not None else self._linked_results()
        self.env.invalidate_all()
        results = results.sudo().exists()
        self.assertEqual(thesis.sudo().points_fin, before['points'])
        self.assertEqual(results.ids, before['result_ids'])
        self.assertEqual(results.mapped('scoring_total'), before['scores'])
        self.assertEqual(results.mapped('irg_tfm_thesis_id').ids, before['links'])
        self.assertEqual(
            self.env['app.gradebook.result'].sudo().search_count([
                ('gradebook_subject_id', '=', self.gradebook_subject.id),
            ]),
            before['count'],
        )
        self.assertEqual(self._audit_messages(thesis).ids, before['messages'])

    def test_resolver_returns_the_only_homeclass_gradebook_subject(self):
        self.assertEqual(
            self.thesis._irg_tfm_resolve_grade_target(),
            self.gradebook_subject,
        )

    def test_resolver_returns_the_only_online_family_gradebook_subject(self):
        case = self._build_case(modality='ONL')
        self.assertEqual(
            case['thesis']._irg_tfm_resolve_grade_target(),
            case['gradebook_subject'],
        )

    def test_resolver_rejects_missing_channel_with_exact_message(self):
        self.course.irg_tfm_channel_id = False
        with self.assertRaises(ValidationError) as caught:
            self.thesis._irg_tfm_resolve_grade_target()
        self.assertEqual(str(caught.exception), 'El curso no tiene configurado Canal TFM.')

    def test_resolver_rejects_zero_or_multiple_subjects_with_exact_message(self):
        for subject_ids in ([], [self.subject.id, self._second_subject().id]):
            self.course.subject_ids = [(6, 0, subject_ids)]
            with self.assertRaises(ValidationError) as caught:
                self.thesis._irg_tfm_resolve_grade_target()
            self.assertEqual(str(caught.exception), SUBJECT_ERROR)

    def _second_subject(self):
        suffix = self._suffix()
        return self.env['op.subject'].create({
            'name': 'Second TFM subject %s' % suffix,
            'code': 'TFM-SECOND-%s' % suffix,
            'course_id': self.course.id,
            'subject_type': 'compulsory',
            'slide_channel_id': self.online_channel.id,
            'gradebook_id': self.template.id,
        })

    def test_resolver_rejects_zero_or_multiple_gradebooks_with_exact_message(self):
        self.gradebook_subject.unlink()
        self.gradebook.unlink()
        with self.assertRaises(ValidationError) as caught:
            self.thesis._irg_tfm_resolve_grade_target()
        self.assertEqual(str(caught.exception), GRADEBOOK_ERROR)

        gradebook_a = self.env['app.gradebook.student'].create({
            'admission_id': self.admission.id,
            'state': 'in_progress',
        })
        gradebook_b = self.env['app.gradebook.student'].create({
            'admission_id': self.admission.id,
            'state': 'in_progress',
        })
        self.env['app.gradebook.subject'].create({
            'gradebook_student_id': gradebook_a.id,
            'op_subject_id': self.subject.id,
        })
        self.env['app.gradebook.subject'].create({
            'gradebook_student_id': gradebook_b.id,
            'op_subject_id': self.subject.id,
        })
        with self.assertRaises(ValidationError) as caught:
            self.thesis._irg_tfm_resolve_grade_target()
        self.assertEqual(str(caught.exception), GRADEBOOK_ERROR)

    def test_resolver_rejects_zero_or_multiple_lines_with_exact_message(self):
        self.gradebook_subject.unlink()
        with self.assertRaises(ValidationError) as caught:
            self.thesis._irg_tfm_resolve_grade_target()
        self.assertEqual(str(caught.exception), LINE_ERROR)

        for _index in range(2):
            self.env['app.gradebook.subject'].create({
                'gradebook_student_id': self.gradebook.id,
                'op_subject_id': self.subject.id,
            })
        with self.assertRaises(ValidationError) as caught:
            self.thesis._irg_tfm_resolve_grade_target()
        self.assertEqual(str(caught.exception), LINE_ERROR)

    def test_forward_write_creates_then_updates_one_stable_link(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        result = self._linked_results()
        self.assertEqual(len(result), 1)
        self.assertEqual(result.gradebook_subject_id, self.gradebook_subject)
        self.assertEqual(result.survey_type, 'exam')
        self.assertEqual(result.scoring_total, 8.5)

        self.thesis.with_user(self.reviewer).write({'points_fin': 9.0})
        linked = self._linked_results()
        self.assertEqual(linked.ids, result.ids)
        self.assertEqual(linked.scoring_total, 9.0)

    def test_forward_refresh_is_scoped_to_the_exact_enrollment_batch(self):
        suffix = self._suffix()
        other_batch = self.env['op.batch'].create({
            'name': 'Other TFM grade sync batch %s' % suffix,
            'code': 'HC2612',
            'course_id': self.course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=60),
        })
        self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': self.course.id,
            'batch_id': other_batch.id,
            'roll_number': 'TFM-GRADE-OTHER-%s' % suffix,
        })

        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})

        self.assertEqual(self._linked_results().scoring_total, 8.5)

    def test_zero_does_not_create_a_result(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 0})
        self.assertFalse(self._linked_results())
        self.assertFalse(self.gradebook_subject.gradebook_result_ids)

    def test_same_value_write_adopts_the_only_existing_exam(self):
        exam = self._create_exam(score=0.0)
        self.thesis.with_user(self.reviewer).write({'points_fin': 0})
        exam.invalidate_recordset()
        self.assertEqual(exam.irg_tfm_thesis_id, self.thesis)
        self.assertEqual(self._linked_results(), exam)

    def test_multiple_unlinked_exams_abort_without_changing_thesis(self):
        self._create_exam(7.0)
        self._create_exam(8.0)
        previous_messages = self._audit_messages().ids
        with self.assertRaises(ValidationError) as caught:
            self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        self.assertEqual(str(caught.exception), EXAM_ERROR)
        self.thesis.invalidate_recordset(['points_fin', 'message_ids'])
        self.assertEqual(self.thesis.points_fin, 0.0)
        self.assertFalse(self._linked_results())
        self.assertEqual(self._audit_messages().ids, previous_messages)

    def test_create_with_explicit_grade_synchronizes_inside_creation(self):
        case = self._build_case(create_thesis=False)
        thesis = self.env['tesis.model'].with_user(self.reviewer).with_context(
            irg_tfm_auto_activation=True,
        ).create(self._thesis_values(case['enrollment'], points_fin=8.5))
        result = self._linked_results(thesis)
        self.assertEqual(result.scoring_total, 8.5)

    def test_create_with_context_default_grade_synchronizes_and_zero_requires_reviewer(self):
        case = self._build_case(create_thesis=False)
        thesis = self.env['tesis.model'].with_user(self.reviewer).with_context(
            irg_tfm_auto_activation=True,
            default_points_fin=8.5,
        ).create(self._thesis_values(case['enrollment']))
        self.assertEqual(self._linked_results(thesis).scoring_total, 8.5)

        ungraded = self._build_case(create_thesis=False)
        with self.assertRaises(AccessError):
            self.env['tesis.model'].with_user(self.internal_user).with_context(
                irg_tfm_auto_activation=True,
                default_points_fin=0,
            ).create(self._thesis_values(ungraded['enrollment']))

    def test_create_without_effective_grade_default_keeps_zero_without_sync(self):
        case = self._build_case(create_thesis=False)

        thesis = self.env['tesis.model'].with_user(
            self.internal_user
        ).with_context(irg_tfm_auto_activation=True).create(
            self._thesis_values(case['enrollment'])
        )

        self.assertEqual(thesis.points_fin, 0.0)
        self.assertFalse(self._linked_results(thesis))

    def test_personal_ir_default_points_requires_reviewer_before_thesis_create(self):
        case = self._build_case(create_thesis=False)
        self.env['ir.default'].with_user(self.internal_user).set(
            'tesis.model',
            'points_fin',
            8.5,
            user_id=True,
        )

        with self.assertRaises(AccessError) as caught:
            self.env['tesis.model'].with_user(self.internal_user).with_context(
                irg_tfm_auto_activation=True,
            ).create(self._thesis_values(case['enrollment']))

        self.assertIn('Solo un Revisor TFM', str(caught.exception))
        self.assertFalse(self.env['tesis.model'].sudo().search([
            ('course_id', '=', case['enrollment'].id),
        ]))

    def test_personal_ir_default_cannot_create_server_owned_result_link(self):
        self.env['ir.default'].with_user(self.gradebook_user).set(
            'app.gradebook.result',
            'irg_tfm_thesis_id',
            self.thesis.id,
            user_id=True,
        )

        with self.assertRaises(AccessError):
            self.env['app.gradebook.result'].with_user(
                self.gradebook_user
            ).create({
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 8.5,
            })

        self.assertFalse(self._linked_results())
        self.assertFalse(self.gradebook_subject.gradebook_result_ids)

    def test_public_result_create_returns_clean_context_and_link_write_is_rejected(self):
        result = self.env['app.gradebook.result'].with_user(
            self.gradebook_user
        ).create({
            'gradebook_subject_id': self.gradebook_subject.id,
            'survey_type': 'exam',
            'scoring_total': 7.0,
        })

        self.assertNotIn('irg_tfm_defer_grade_trigger', result.env.context)
        with self.assertRaises(AccessError):
            result.with_user(self.gradebook_user).write({
                'irg_tfm_thesis_id': self.thesis.id,
            })
        # The reverse coordinator owns this link: the client may not supply it,
        # but the server computes it for an exam created on the TFM line.
        result.invalidate_recordset(['irg_tfm_thesis_id'])
        self.assertEqual(result.irg_tfm_thesis_id, self.thesis)

    def test_public_thesis_grade_requires_reviewer_even_with_forged_context(self):
        actors = (
            self.internal_user,
            self.portal_user,
            self.gradebook_user,
            self.reviewer,
        )
        for actor in actors:
            with self.subTest(actor=actor.login), self.assertRaises(AccessError):
                self.thesis.with_user(actor).with_context(
                    irg_tfm_grade_sync_origin='thesis',
                ).write({'points_fin': 8.5})
        self.thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(self.thesis.points_fin, 0.0)

    def test_reserved_sync_and_defer_context_is_rejected_on_all_public_boundaries(self):
        actors = (
            self.internal_user,
            self.portal_user,
            self.gradebook_user,
            self.reviewer,
        )
        reserved_contexts = (
            {'irg_tfm_grade_sync_origin': 'thesis'},
            {'irg_tfm_defer_grade_trigger': True},
            {'irg_tfm_defer_grade_trigger': False},
            {'irg_tfm_thesis_id': self.thesis.id},
            {'default_irg_tfm_thesis_id': self.thesis.id},
        )
        create_case = self._build_case(create_thesis=False)
        exam = self._create_exam(7.0)
        before_result_ids = self.env['app.gradebook.result'].sudo().search([
            ('gradebook_subject_id', '=', self.gradebook_subject.id),
        ]).ids
        for actor in actors:
            for reserved_context in reserved_contexts:
                label = (actor.login, reserved_context)
                with self.subTest(boundary='thesis-write', case=label):
                    with self.assertRaises(AccessError):
                        self.thesis.with_user(actor).with_context(
                            **reserved_context
                        ).write({'points_fin': 8.5})
                with self.subTest(boundary='thesis-create', case=label):
                    with self.assertRaises(AccessError):
                        self.env['tesis.model'].with_user(actor).with_context(
                            irg_tfm_auto_activation=True,
                            **reserved_context
                        ).create(self._thesis_values(
                            create_case['enrollment'],
                            points_fin=8.5,
                        ))
                with self.subTest(boundary='result-write', case=label):
                    with self.assertRaises(AccessError):
                        exam.with_user(actor).with_context(
                            **reserved_context
                        ).write({'scoring_total': 8.5})
                with self.subTest(boundary='result-create', case=label):
                    with self.assertRaises(AccessError):
                        self.env['app.gradebook.result'].with_user(actor).with_context(
                            **reserved_context
                        ).create({
                            'gradebook_subject_id': self.gradebook_subject.id,
                            'survey_type': 'exam',
                            'scoring_total': 8.5,
                        })

        self.env.invalidate_all()
        self.assertEqual(self.thesis.points_fin, 0.0)
        self.assertEqual(exam.scoring_total, 7.0)
        self.assertFalse(exam.irg_tfm_thesis_id)
        self.assertFalse(self.env['tesis.model'].sudo().search([
            ('course_id', '=', create_case['enrollment'].id),
        ]))
        self.assertEqual(
            self.env['app.gradebook.result'].sudo().search([
                ('gradebook_subject_id', '=', self.gradebook_subject.id),
            ]).ids,
            before_result_ids,
        )

    def test_client_link_payload_is_rejected_on_thesis_and_result_create_write(self):
        actors = (
            self.internal_user,
            self.portal_user,
            self.gradebook_user,
            self.reviewer,
        )
        create_case = self._build_case(create_thesis=False)
        exam = self._create_exam(7.0)
        for actor in actors:
            for link_value in (False, self.thesis.id):
                label = (actor.login, link_value)
                with self.subTest(boundary='thesis-write', case=label):
                    with self.assertRaises(AccessError):
                        self.thesis.with_user(actor).write({
                            'irg_tfm_thesis_id': link_value,
                        })
                with self.subTest(boundary='thesis-create', case=label):
                    with self.assertRaises(AccessError):
                        self.env['tesis.model'].with_user(actor).create(
                            dict(
                                self._thesis_values(create_case['enrollment']),
                                irg_tfm_thesis_id=link_value,
                            )
                        )
                with self.subTest(boundary='result-write', case=label):
                    with self.assertRaises(AccessError):
                        exam.with_user(actor).write({
                            'irg_tfm_thesis_id': link_value,
                        })
                with self.subTest(boundary='result-create', case=label):
                    with self.assertRaises(AccessError):
                        self.env['app.gradebook.result'].with_user(actor).create({
                            'gradebook_subject_id': self.gradebook_subject.id,
                            'survey_type': 'exam',
                            'scoring_total': 8.5,
                            'irg_tfm_thesis_id': link_value,
                        })

        self.env.invalidate_all()
        self.assertFalse(exam.irg_tfm_thesis_id)
        self.assertFalse(self.env['tesis.model'].sudo().search([
            ('course_id', '=', create_case['enrollment'].id),
        ]))

    def test_linked_result_relationships_are_server_owned_even_when_value_is_false(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        result = self._linked_results()
        attempts = (
            {'irg_tfm_thesis_id': False},
            {'irg_tfm_thesis_id': self.thesis.id},
            {'survey_type': False},
            {'survey_type': 'exam'},
            {'gradebook_subject_id': False},
            {'gradebook_subject_id': self.gradebook_subject.id},
        )
        for actor in (
            self.internal_user,
            self.portal_user,
            self.gradebook_user,
            self.reviewer,
        ):
            for values in attempts:
                with self.subTest(actor=actor.login, values=values):
                    with self.assertRaises(AccessError):
                        result.with_user(actor).write(values)
        result.invalidate_recordset()
        self.assertEqual(result.irg_tfm_thesis_id, self.thesis)
        self.assertEqual(result.survey_type, 'exam')
        self.assertEqual(result.gradebook_subject_id, self.gradebook_subject)

    def test_score_must_be_finite_and_in_the_exact_tfm_scale(self):
        for score in (-1.0, 0.5, 10.1, float('nan'), float('inf'), float('-inf')):
            with self.subTest(score=score), self.assertRaises(ValidationError):
                self.thesis.with_user(self.reviewer).write({'points_fin': score})
        for score in (0.0, 1.0, 8.5, 10.0):
            with self.subTest(score=score):
                self.thesis.with_user(self.reviewer).write({'points_fin': score})
                self.thesis.invalidate_recordset(['points_fin'])
                self.assertEqual(self.thesis.points_fin, score)

    def test_reread_rejects_changed_enrollment_and_admission_batch_from_snapshot(self):
        identity = self.thesis._irg_tfm_resolve_grade_identity(
            self.enrollment,
            self.thesis,
        )
        suffix = self._suffix()
        other_batch = self.env['op.batch'].create({
            'name': 'Concurrent TFM batch %s' % suffix,
            'code': 'HC2612',
            'course_id': self.course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=60),
        })
        self.env.cr.execute(
            'UPDATE op_student_course SET batch_id = %s WHERE id = %s',
            [other_batch.id, self.enrollment.id],
        )
        self.env.cr.execute(
            'UPDATE op_admission SET batch_id = %s WHERE id = %s',
            [other_batch.id, self.admission.id],
        )

        with self.assertRaises(ValidationError) as caught:
            self.thesis._irg_tfm_reresolve_after_locks(identity)

        self.assertEqual(str(caught.exception), CONCURRENT_MAPPING_ERROR)

    def test_reread_invalidates_every_course_subject_candidate(self):
        foreign_channel = self.env['slide.channel'].create({
            'name': 'Initially unrelated TFM channel %s' % self._suffix(),
        })
        second_subject = self.env['op.subject'].create({
            'name': 'Concurrent second TFM subject %s' % self._suffix(),
            'code': 'TFM-CONCURRENT-%s' % self._suffix(),
            'course_id': self.course.id,
            'subject_type': 'compulsory',
            'slide_channel_id': foreign_channel.id,
            'gradebook_id': self.template.id,
        })
        self.course.write({'subject_ids': [(4, second_subject.id)]})
        identity = self.thesis._irg_tfm_resolve_grade_identity(
            self.enrollment,
            self.thesis,
        )
        self.env.cr.execute(
            'UPDATE op_subject SET slide_channel_id = %s WHERE id = %s',
            [self.online_channel.id, second_subject.id],
        )

        with self.assertRaises(ValidationError) as caught:
            self.thesis._irg_tfm_reresolve_after_locks(identity)

        self.assertEqual(str(caught.exception), SUBJECT_ERROR)

    def test_clamp_policy_is_rejected_without_partial_state(self):
        self.template.grading_scale = 8.0
        previous_messages = self._audit_messages().ids

        with self.assertRaises(ValidationError) as caught:
            self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})

        self.assertEqual(str(caught.exception), NORMALIZATION_ERROR)
        self.env.invalidate_all()
        self.assertEqual(self.thesis.points_fin, 0.0)
        self.assertFalse(self._linked_results())
        self.assertEqual(self._audit_messages().ids, previous_messages)

    def test_post_hook_score_discrepancy_rolls_back_all_mutations(self):
        exam = self._create_exam(7.0)
        before = {
            'points': self.thesis.points_fin,
            'score': exam.scoring_total,
            'link': exam.irg_tfm_thesis_id.id,
            'count': self.env['app.gradebook.result'].sudo().search_count([
                ('gradebook_subject_id', '=', self.gradebook_subject.id),
            ]),
            'messages': self._audit_messages().ids,
        }
        result_class = type(exam)
        original_internal_write = result_class._irg_tfm_internal_write

        def write_then_transform(records, values):
            outcome = original_internal_write(records, values)
            records.flush_recordset(['scoring_total'])
            records.env.cr.execute(
                'UPDATE app_gradebook_result SET scoring_total = %s '
                'WHERE id IN %s',
                [8.0, tuple(records.ids)],
            )
            return outcome

        with patch.object(
            result_class,
            '_irg_tfm_internal_write',
            write_then_transform,
        ):
            with self.assertRaises(ValidationError) as caught:
                self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        self.assertEqual(str(caught.exception), NORMALIZATION_ERROR)

        self.env.invalidate_all()
        exam = self.env['app.gradebook.result'].sudo().browse(exam.id)
        thesis = self.env['tesis.model'].sudo().browse(self.thesis.id)
        self.assertEqual(thesis.points_fin, before['points'])
        self.assertEqual(exam.scoring_total, before['score'])
        self.assertEqual(exam.irg_tfm_thesis_id.id, before['link'])
        self.assertEqual(
            self.env['app.gradebook.result'].sudo().search_count([
                ('gradebook_subject_id', '=', self.gradebook_subject.id),
            ]),
            before['count'],
        )
        self.assertEqual(self._audit_messages(thesis).ids, before['messages'])

    def test_rounding_policy_rolls_back_grade_link_count_and_audit(self):
        exam = self._create_exam(7.0)
        self.template.round_subject_result = True
        before = {
            'points': self.thesis.points_fin,
            'score': exam.scoring_total,
            'link': exam.irg_tfm_thesis_id.id,
            'count': self.env['app.gradebook.result'].sudo().search_count([
                ('gradebook_subject_id', '=', self.gradebook_subject.id),
            ]),
            'messages': self._audit_messages().ids,
        }
        with self.assertRaises(ValidationError) as caught:
            self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        self.assertEqual(str(caught.exception), NORMALIZATION_ERROR)
        self.env.invalidate_all()
        exam = self.env['app.gradebook.result'].sudo().browse(exam.id)
        thesis = self.env['tesis.model'].sudo().browse(self.thesis.id)
        self.assertEqual(thesis.points_fin, before['points'])
        self.assertEqual(exam.scoring_total, before['score'])
        self.assertEqual(exam.irg_tfm_thesis_id.id, before['link'])
        self.assertEqual(
            self.env['app.gradebook.result'].sudo().search_count([
                ('gradebook_subject_id', '=', self.gradebook_subject.id),
            ]),
            before['count'],
        )
        self.assertEqual(self._audit_messages(thesis).ids, before['messages'])

    def test_audit_uses_original_actor_server_origin_values_and_stable_result(self):
        exam = self._create_exam(7.0)
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        message = self._audit_messages()
        self.assertEqual(len(message), 1)
        body = message.body
        self.assertIn(self.reviewer.display_name, body)
        self.assertIn('uid=%s' % self.reviewer.id, body)
        self.assertIn('origen=thesis', body)
        self.assertIn('tesis=0.0', body)
        self.assertIn('libreta=7.0', body)
        self.assertIn('nuevo=8.5', body)
        self.assertIn('resultado=%s' % exam.id, body)

        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        self.assertEqual(self._audit_messages().ids, message.ids)

    def test_reverse_write_on_linked_result_updates_points_fin(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        thesis = self.thesis
        linked_result = self._linked_results().with_user(self.gradebook_user)

        linked_result.write({'scoring_total': 9.0})

        thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(thesis.points_fin, 9.0)
        self.assertEqual(self._linked_results().ids, linked_result.ids)

    def test_reverse_create_links_and_synchronizes_the_only_exam(self):
        thesis = self.thesis

        new_result = self.env['app.gradebook.result'].create({
            'gradebook_subject_id': self.gradebook_subject.id,
            'survey_type': 'exam',
            'scoring_total': 7.5,
            'description': 'TFM',
        })

        self.assertEqual(new_result.irg_tfm_thesis_id, thesis)
        thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(thesis.points_fin, 7.5)
        self.assertEqual(self._linked_results().ids, new_result.ids)

    def test_forward_and_reverse_sync_run_once_each_without_recursion(self):
        counters, patchers = self._sync_counters()

        with ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
            self.assertEqual(counters, {'forward': 1, 'reverse': 0})
            self._linked_results().with_user(self.gradebook_user).write({
                'scoring_total': 9.0,
            })

        self.assertEqual(counters, {'forward': 1, 'reverse': 1})
        self.thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(self.thesis.points_fin, 9.0)
        self.assertEqual(len(self._audit_messages()), 2)

    def test_ordinary_subject_results_stay_outside_the_reverse_sync(self):
        ordinary_line = self._ordinary_line()
        counters, patchers = self._sync_counters()

        with ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            ordinary = self.env['app.gradebook.result'].create({
                'gradebook_subject_id': ordinary_line.id,
                'survey_type': 'exam',
                'scoring_total': 9.0,
            })
            ordinary.write({'scoring_total': 6.0})
            assignment = self.env['app.gradebook.result'].create({
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'assignment',
                'scoring_total': 4.0,
            })
            assignment.write({'scoring_total': 5.0})

        self.assertEqual(counters, {'forward': 0, 'reverse': 0})
        self.assertFalse(ordinary.irg_tfm_thesis_id)
        self.assertFalse(assignment.irg_tfm_thesis_id)
        self.thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(self.thesis.points_fin, 0.0)
        self.assertFalse(self._audit_messages())

    def test_second_exam_is_not_silently_linked_on_the_tfm_line(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        linked = self._linked_results()
        before = self._reverse_state(linked)

        with self.assertRaises(ValidationError) as caught:
            self.env['app.gradebook.result'].create({
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 7.0,
            })

        self.assertEqual(str(caught.exception), LINKED_EXAM_ERROR)
        self._assert_reverse_state_unchanged(before, linked)

    def test_unlinked_exam_ambiguity_is_not_silently_linked_on_create(self):
        self._create_exam(7.0)
        before = self._reverse_state(self.env['app.gradebook.result'])

        with self.assertRaises(ValidationError) as caught:
            self.env['app.gradebook.result'].create({
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 8.0,
            })

        self.assertEqual(str(caught.exception), EXAM_ERROR)
        self._assert_reverse_state_unchanged(
            before,
            self.env['app.gradebook.result'],
        )

    def test_linked_result_cannot_move_to_another_subject_or_thesis(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        linked = self._linked_results()
        other_line = self._ordinary_line()
        other_case = self._build_case()
        before = self._reverse_state(linked)
        attempts = (
            {'gradebook_subject_id': other_line.id},
            {'gradebook_subject_id': other_case['gradebook_subject'].id},
            {'irg_tfm_thesis_id': other_case['thesis'].id},
            {'survey_type': 'assignment'},
        )

        for values in attempts:
            with self.subTest(values=values), self.assertRaises(AccessError):
                linked.with_user(self.gradebook_user).write(values)
            with self.subTest(values=values, actor='sudo'):
                with self.assertRaises(AccessError):
                    linked.sudo().write(values)

        self._assert_reverse_state_unchanged(before, linked)

    def test_linked_result_cannot_be_deleted_through_any_route(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        linked = self._linked_results()
        before = self._reverse_state(linked)
        routes = (
            (linked, 'unlink', None),
            (self.gradebook_subject, 'write', {
                'gradebook_result_ids': [(2, linked.id)],
            }),
            (self.gradebook_subject, 'write', {
                'gradebook_result_ids': [(3, linked.id)],
            }),
            (self.gradebook_subject, 'unlink', None),
            (self.gradebook, 'write', {
                'gradebook_subject_ids': [(2, self.gradebook_subject.id)],
            }),
            (self.gradebook, 'unlink', None),
            (self.admission, 'unlink', None),
            (self.enrollment, 'unlink', None),
            (self.thesis, 'unlink', None),
        )

        for record, operation, values in routes:
            with self.subTest(model=record._name, operation=operation, values=values):
                with self.assertRaises(AccessError):
                    if operation == 'unlink':
                        record.sudo().unlink()
                    else:
                        record.sudo().write(values)

        self._assert_reverse_state_unchanged(before, linked)

    def test_linked_parent_identity_reassignment_is_rejected_server_side(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        linked = self._linked_results()
        other = self._build_case(create_thesis=False)
        before = self._reverse_state(linked)
        attempts = (
            (self.gradebook_subject, {'op_subject_id': other['subject'].id}),
            (self.gradebook_subject, {
                'gradebook_student_id': other['gradebook'].id,
            }),
            (self.gradebook, {'admission_id': other['admission'].id}),
            (self.gradebook, {
                'gradebook_subject_ids': [(6, 0, [])],
            }),
            (self.admission, {'student_id': other['student'].id}),
            (self.admission, {'course_id': other['course'].id}),
            (self.admission, {'batch_id': other['batch'].id}),
            (self.enrollment, {'student_id': other['student'].id}),
            (self.enrollment, {'course_id': other['course'].id}),
            (self.enrollment, {'batch_id': other['batch'].id}),
            (self.thesis, {'course_id': other['enrollment'].id}),
        )

        for record, values in attempts:
            with self.subTest(model=record._name, values=values):
                with self.assertRaises(AccessError):
                    record.sudo().write(values)

        self._assert_reverse_state_unchanged(before, linked)

    def test_reverse_entry_point_enforces_the_exact_tfm_scale(self):
        for score in (-1.0, 0.5, 10.1, float('nan'), float('inf'), float('-inf')):
            with self.subTest(score=score, boundary='create'):
                with self.assertRaises(ValidationError):
                    self.env['app.gradebook.result'].create({
                        'gradebook_subject_id': self.gradebook_subject.id,
                        'survey_type': 'exam',
                        'scoring_total': score,
                    })
        self.assertFalse(self._linked_results())
        self.assertFalse(self.env['app.gradebook.result'].sudo().search_count([
            ('gradebook_subject_id', '=', self.gradebook_subject.id),
        ]))

        linked = self.env['app.gradebook.result'].create({
            'gradebook_subject_id': self.gradebook_subject.id,
            'survey_type': 'exam',
            'scoring_total': 1.0,
        })
        self.thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(self.thesis.points_fin, 1.0)
        for score in (0.0, 7.5, 10.0):
            with self.subTest(score=score, boundary='write'):
                linked.write({'scoring_total': score})
                self.thesis.invalidate_recordset(['points_fin'])
                self.assertEqual(self.thesis.points_fin, score)
        for score in (-1.0, 0.5, 10.1, float('nan'), float('inf'), float('-inf')):
            with self.subTest(score=score, boundary='write-invalid'):
                with self.assertRaises(ValidationError):
                    linked.write({'scoring_total': score})
        self.env.invalidate_all()
        self.assertEqual(linked.scoring_total, 10.0)
        self.assertEqual(self.thesis.points_fin, 10.0)

    def test_reverse_rounding_policy_rolls_back_grade_link_count_and_audit(self):
        self.template.round_subject_result = True
        before = self._reverse_state(self.env['app.gradebook.result'])

        with self.assertRaises(ValidationError) as caught:
            self.env['app.gradebook.result'].create({
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 8.5,
            })

        self.assertEqual(str(caught.exception), NORMALIZATION_ERROR)
        self._assert_reverse_state_unchanged(
            before,
            self.env['app.gradebook.result'],
        )

    def test_reverse_clamp_policy_rolls_back_without_partial_state(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        linked = self._linked_results()
        before = self._reverse_state(linked)
        self.template.grading_scale = 8.0

        with self.assertRaises(ValidationError) as caught:
            linked.with_user(self.gradebook_user).write({'scoring_total': 9.0})

        self.assertEqual(str(caught.exception), NORMALIZATION_ERROR)
        self.template.grading_scale = 10.0
        self._assert_reverse_state_unchanged(before, linked)

    def test_reverse_failure_caught_by_the_caller_changes_nothing(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        linked = self._linked_results()
        before = self._reverse_state(linked)
        self.course.irg_tfm_channel_id = False

        try:
            linked.with_user(self.gradebook_user).write({'scoring_total': 9.0})
        except (AccessError, ValidationError):
            pass

        self.course.irg_tfm_channel_id = self.home_channel
        self._assert_reverse_state_unchanged(before, linked)

    def test_reverse_audit_uses_original_actor_gradebook_origin_and_values(self):
        result = self.env['app.gradebook.result'].with_user(
            self.gradebook_user
        ).create({
            'gradebook_subject_id': self.gradebook_subject.id,
            'survey_type': 'exam',
            'scoring_total': 7.5,
        })

        message = self._audit_messages()
        self.assertEqual(len(message), 1)
        body = message.body
        self.assertIn(self.gradebook_user.display_name, body)
        self.assertIn('uid=%s' % self.gradebook_user.id, body)
        self.assertIn('origen=gradebook', body)
        self.assertIn('tesis=0.0', body)
        self.assertIn('nuevo=7.5', body)
        self.assertIn('resultado=%s' % result.id, body)
        self.assertEqual(
            message.author_id,
            self.gradebook_user.partner_id,
        )

        result.with_user(self.gradebook_user).write({'scoring_total': 7.5})
        self.assertEqual(self._audit_messages().ids, message.ids)

    def test_reverse_sync_refreshes_the_derived_enrollment_hook_once(self):
        refreshed = []
        result_class = type(self.env['app.gradebook.result'])
        original = result_class._irg_tfm_refresh_affected_enrollments

        def counted(records, subjects, locked_enrollments=None):
            refreshed.append(subjects.ids)
            return original(
                records,
                subjects,
                locked_enrollments=locked_enrollments,
            )

        with patch.object(
            result_class,
            '_irg_tfm_refresh_affected_enrollments',
            counted,
        ):
            self.env['app.gradebook.result'].create({
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 7.5,
            })

        self.assertEqual(refreshed, [self.gradebook_subject.ids])
        self.gradebook_subject.invalidate_recordset(['final_subject_note'])
        self.assertEqual(self.gradebook_subject.final_subject_note, 7.5)

    def test_one2many_create_list_links_tfm_exam_and_keeps_ordinary_row(self):
        ordinary_line = self._ordinary_line()
        created = self.env['app.gradebook.result'].with_user(
            self.gradebook_user
        ).create([
            {
                'gradebook_subject_id': ordinary_line.id,
                'survey_type': 'exam',
                'scoring_total': 6.0,
                'description': 'Ordinary exam',
            },
            {
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 8.5,
                'description': 'TFM exam',
            },
        ])

        self.assertEqual(len(created), 2)
        ordinary = created.filtered(
            lambda result: result.gradebook_subject_id == ordinary_line
        )
        tfm = created.filtered(
            lambda result: result.gradebook_subject_id == self.gradebook_subject
        )
        self.assertEqual(len(ordinary), 1)
        self.assertFalse(ordinary.irg_tfm_thesis_id)
        self.assertEqual(ordinary.scoring_total, 6.0)
        self.assertEqual(tfm.irg_tfm_thesis_id, self.thesis)
        self.assertEqual(tfm.scoring_total, 8.5)
        self.thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(self.thesis.points_fin, 8.5)

    def test_one2many_create_list_tfm_before_ordinary_still_links(self):
        other = self._build_case(create_thesis=False)
        ordinary_subject = self.env['op.subject'].create({
            'name': 'Ordinary subject %s' % self._suffix(),
            'code': 'TFM-ORD-%s' % self._suffix(),
            'course_id': other['course'].id,
            'subject_type': 'compulsory',
            'slide_channel_id': self.env['slide.channel'].create({
                'name': 'Ordinary channel %s' % self._suffix(),
            }).id,
            'gradebook_id': other['template'].id,
        })
        other['course'].write({'subject_ids': [(4, ordinary_subject.id)]})
        ordinary_line = self.env['app.gradebook.subject'].create({
            'gradebook_student_id': other['gradebook'].id,
            'op_subject_id': ordinary_subject.id,
        })
        self.assertNotEqual(self.enrollment.id, other['enrollment'].id)
        created = self.env['app.gradebook.result'].with_user(
            self.gradebook_user
        ).create([
            {
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 8.5,
                'description': 'TFM exam first',
            },
            {
                'gradebook_subject_id': ordinary_line.id,
                'survey_type': 'exam',
                'scoring_total': 6.0,
                'description': 'Ordinary exam second',
            },
        ])

        self.assertEqual(created[0].irg_tfm_thesis_id, self.thesis)
        self.assertEqual(created[0].scoring_total, 8.5)
        self.assertFalse(created[1].irg_tfm_thesis_id)
        self.assertEqual(created[1].scoring_total, 6.0)
        self.thesis.invalidate_recordset(['points_fin'])
        self.assertEqual(self.thesis.points_fin, 8.5)

    def test_one2many_create_list_rejects_client_link_on_each_payload(self):
        ordinary_line = self._ordinary_line()
        payloads = [
            {
                'gradebook_subject_id': ordinary_line.id,
                'survey_type': 'exam',
                'scoring_total': 6.0,
            },
            {
                'gradebook_subject_id': self.gradebook_subject.id,
                'survey_type': 'exam',
                'scoring_total': 8.5,
            },
        ]
        for index in range(len(payloads)):
            mixed = [dict(item) for item in payloads]
            mixed[index]['irg_tfm_thesis_id'] = self.thesis.id
            with self.assertRaises(AccessError):
                self.env['app.gradebook.result'].with_user(
                    self.gradebook_user
                ).create(mixed)
        self.assertFalse(self._linked_results())

    def test_course_and_convocation_cannot_be_written_together(self):
        convocation = self.env['irg.tfm.convocatoria'].create({
            'name': 'TFM combined write %s' % self._suffix(),
            'code': 'TFM-COMB-%s' % self._suffix(),
        })
        other = self._build_case(create_thesis=False)
        before_course = self.thesis.course_id
        with self.assertRaises(ValidationError) as caught:
            self.thesis.write({
                'course_id': other['enrollment'].id,
                'irg_tfm_convocation_id': convocation.id,
            })
        self.assertEqual(str(caught.exception), IDENTITY_CONVOCATION_ERROR)
        self.thesis.invalidate_recordset([
            'course_id', 'irg_tfm_convocation_id',
        ])
        self.assertEqual(self.thesis.course_id, before_course)
        self.assertFalse(self.thesis.irg_tfm_convocation_id)

    def test_mixed_result_write_is_rejected_without_partial_state(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        linked = self._linked_results()
        ordinary = self.env['app.gradebook.result'].create({
            'gradebook_subject_id': self._ordinary_line().id,
            'survey_type': 'exam',
            'scoring_total': 4.0,
        })
        before = self._reverse_state(linked)
        ordinary_score = ordinary.scoring_total

        with self.assertRaises(ValidationError) as caught:
            (linked | ordinary).with_user(self.gradebook_user).write({
                'scoring_total': 9.0,
            })

        self.assertEqual(str(caught.exception), MIXED_RESULT_ERROR)
        self._assert_reverse_state_unchanged(before, linked)
        ordinary.invalidate_recordset(['scoring_total'])
        self.assertEqual(ordinary.scoring_total, ordinary_score)

    def test_link_guard_scope_uses_exact_enrollment_triples(self):
        self.thesis.with_user(self.reviewer).write({'points_fin': 8.5})
        other = self._build_case(create_thesis=False)
        extra_enrollment = self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': other['course'].id,
            'batch_id': other['batch'].id,
            'roll_number': 'TFM-GUARD-EXTRA-%s' % self._suffix(),
        })
        stranger_enrollment = self.env['op.student.course'].create({
            'student_id': other['student'].id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'roll_number': 'TFM-GUARD-STRANGER-%s' % self._suffix(),
        })
        mixed = extra_enrollment | stranger_enrollment
        scope = self.env['tesis.model']._irg_tfm_link_guard_scope(mixed)
        self.assertFalse(scope['linked_results'])
        mixed.write({
            'course_id': extra_enrollment.course_id.id,
        })
        self.assertTrue(extra_enrollment.exists())
        self.assertTrue(stranger_enrollment.exists())
        self.assertEqual(self._linked_results().irg_tfm_thesis_id, self.thesis)
