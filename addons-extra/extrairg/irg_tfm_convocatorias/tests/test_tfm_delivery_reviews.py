from pathlib import Path
from xml.etree import ElementTree

from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import HttpCase, TransactionCase, tagged

from .test_tfm_deliveries import PDF_BYTES, TfmFixtureMixin


@tagged('post_install', '-at_install')
class TestTfmDeliveryReview(TfmFixtureMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        helper = TfmFixtureMixin()
        helper.env = cls.env
        cls.reviewer = cls._internal_user('TFM reviewer', [
            cls.env.ref('irg_tfm_convocatorias.group_tfm_reviewer').id,
        ])
        cls.internal_user = cls._internal_user('TFM internal user', [
            cls.env.ref('base.group_user').id,
        ])
        cls.portal_user = cls._internal_user('TFM portal user', [
            cls.env.ref('base.group_portal').id,
        ])
        _owner, _student, _course, _enrollment, cls.thesis = helper._portal_case()
        cls.thesis.write({'irg_tfm_convocation_id': helper._convocation().id})
        cls.partial = cls.env['irg.tfm.entrega']._irg_create_locked_submission(
            cls.thesis,
            'partial',
            PDF_BYTES,
            'partial.pdf',
            'application/pdf',
        )

    @classmethod
    def _internal_user(cls, name, group_ids):
        suffix = TfmFixtureMixin()._suffix()
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': name,
            'login': 'tfm.review.%s@example.test' % suffix,
            'groups_id': [Command.set(group_ids)],
        })

    def _delivery(self, thesis, stage, filename):
        return self.env['irg.tfm.entrega']._irg_create_locked_submission(
            thesis,
            stage,
            PDF_BYTES,
            filename,
            'application/pdf',
        )

    def _create_review(self, **overrides):
        values = {
            'delivery_id': self.partial.id,
            'state': 'corrections',
            'comment': 'Corrige la metodología y vuelve a entregar.',
        }
        values.update(overrides)
        return self.env['irg.tfm.entrega.revision'].with_user(self.reviewer).create(values)

    def test_backend_view_contract_limits_delivery_history_to_review_actions(self):
        """A missing button or editable identity field breaks reviewer workflow."""
        addon = Path(__file__).resolve().parents[1]
        thesis_views = ElementTree.parse(addon / 'views/tesis_model_views.xml').getroot()
        review_views = ElementTree.parse(
            addon / 'views/irg_tfm_entrega_revision_views.xml',
        ).getroot()
        submission_tree = thesis_views.find(
            ".//field[@name='irg_tfm_submission_ids']/tree",
        )
        review_form = review_views.find(".//field[@name='arch']/form")

        self.assertTrue(submission_tree)
        self.assertTrue(review_form)
        self.assertEqual(
            thesis_views.find(".//field[@name='irg_tfm_submission_ids']").get('readonly'),
            '1',
        )
        self.assertEqual(submission_tree.get('create'), 'false')
        self.assertEqual(submission_tree.get('delete'), 'false')
        self.assertTrue(
            {'irg_tfm_review_state', 'irg_tfm_reviewed_at'}.issubset({
                field.get('name') for field in submission_tree.findall('field')
            }),
        )
        self.assertTrue(any(
            button.get('name') == 'action_open_tfm_review'
            and button.get('type') == 'object'
            and button.get('string') == 'Revisar entrega'
            and button.get('groups') == 'irg_tfm_convocatorias.group_tfm_reviewer'
            and button.get('attrs') == (
                "{'invisible': [('stage', 'not in', ['partial', 'final'])]}"
            )
            for button in submission_tree.findall('button')
        ))
        self.assertEqual(
            [field.get('name') for field in review_form.findall('.//sheet//field')],
            [
                'delivery_id', 'attachment_id', 'student_id', 'version', 'state', 'comment',
                'reviewed_by', 'reviewed_at',
            ],
        )
        for name in (
            'delivery_id', 'attachment_id', 'student_id', 'version', 'reviewed_by', 'reviewed_at',
        ):
            self.assertEqual(review_form.find(".//field[@name='%s']" % name).get('readonly'), '1')
        for name in ('state', 'comment'):
            self.assertIsNone(review_form.find(".//field[@name='%s']" % name).get('readonly'))

    def test_portal_feedback_contract_is_scoped_readonly_and_escaped(self):
        """A broad sudo, editable field or raw comment breaks portal isolation."""
        addon = Path(__file__).resolve().parents[1]
        portal_source = (addon / 'controllers/portal.py').read_text(encoding='utf-8-sig')
        portal_root = ElementTree.parse(
            addon / 'views/tfm_portal_templates.xml',
        ).getroot()
        submission = portal_root.find(".//template[@id='tfm_submission_section']")
        submission_xml = ElementTree.tostring(submission, encoding='unicode')

        self.assertIn("('delivery_id', 'in', deliveries.ids)", portal_source)
        self.assertIn("fields=['delivery_id', 'state', 'comment']", portal_source)
        self.assertIn("'review_state_labels'", portal_source)
        self.assertIn("'delivery_reviews'", portal_source)
        self.assertIn("delivery_reviews.get(delivery.id)", submission_xml)
        self.assertIn("review_state_labels.get(review.get('state'))", submission_xml)
        self.assertIn('t-esc="review.get(\'comment\')"', submission_xml)
        self.assertNotIn('t-raw=', submission_xml)
        editable_names = {
            element.get('name')
            for element in submission.findall('.//*[@name]')
        }
        self.assertTrue({'review_state', 'review_comment'}.isdisjoint(editable_names))
        self.assertNotIn('message_ids', submission_xml)
        self.assertNotRegex(
            portal_source,
            r"['\"][^'\"]*/review(?:/[^'\"]*)?['\"]",
        )

    def test_published_review_stamps_actor_and_time_and_cannot_be_deleted(self):
        before = fields.Datetime.now()
        review = self._create_review()

        self.assertEqual(review.reviewed_by, self.reviewer)
        self.assertTrue(review.reviewed_at)
        self.assertGreaterEqual(review.reviewed_at, before)
        self.assertEqual(self.partial.irg_tfm_review_id, review)
        with self.assertRaises(AccessError):
            review.with_user(self.reviewer).unlink()

    def test_delivery_accepts_only_one_review(self):
        self._create_review(state='pending', comment=False)

        with self.assertRaises(ValidationError):
            self._create_review(state='pending', comment=False)

    def test_outline_delivery_cannot_be_reviewed(self):
        _owner, _student, _course, _enrollment, thesis = self._portal_case()
        outline = self._delivery(thesis, 'outline', 'outline.pdf')

        with self.assertRaises(ValidationError):
            self._create_review(delivery_id=outline.id)

    def test_inactive_thesis_delivery_cannot_be_reviewed(self):
        self.thesis.write({'irg_tfm_activated_at': False})

        with self.assertRaises(ValidationError):
            self._create_review()

    def test_corrections_require_a_nonempty_comment_on_create_and_write(self):
        for comment in (False, '', '   '):
            with self.subTest(operation='create', comment=comment):
                with self.assertRaises(ValidationError):
                    self._create_review(comment=comment)

        review = self._create_review(state='pending', comment=False)
        for comment in (False, '', '   '):
            with self.subTest(operation='write', comment=comment):
                with self.assertRaises(ValidationError):
                    review.write({'state': 'corrections', 'comment': comment})

    def test_review_delivery_cannot_be_reassigned(self):
        review = self._create_review(state='pending', comment=False)
        other = self._delivery(self.thesis, 'partial', 'partial-v2.pdf')

        with self.assertRaises(AccessError):
            review.write({'delivery_id': other.id})

    def test_internal_user_without_reviewer_group_cannot_create_or_write(self):
        Review = self.env['irg.tfm.entrega.revision'].with_user(self.internal_user)
        with self.assertRaises(AccessError):
            Review.create({'delivery_id': self.partial.id, 'state': 'pending'})

        review = self._create_review(state='pending', comment=False)
        with self.assertRaises(AccessError):
            review.with_user(self.internal_user).write({'state': 'approved'})

    def test_internal_user_reads_only_delivery_summary_without_review_acl(self):
        review = self._create_review(state='approved')
        delivery = self.partial.with_user(self.internal_user)

        self.assertEqual(delivery.irg_tfm_review_state, 'approved')
        self.assertEqual(delivery.irg_tfm_reviewed_at, review.reviewed_at)
        self.assertFalse(delivery.irg_tfm_review_id)
        with self.assertRaises(AccessError):
            self.env['irg.tfm.entrega.revision'].with_user(self.internal_user).search([])

    def test_review_link_cache_is_isolated_for_internal_and_reviewer_in_both_orders(self):
        review = self._create_review(state='approved')
        summary_fields = [
            'irg_tfm_review_id',
            'irg_tfm_review_state',
            'irg_tfm_reviewed_at',
        ]

        def assert_summary(user, expected_review):
            delivery = self.partial.with_user(user)
            if expected_review:
                self.assertEqual(delivery.irg_tfm_review_id, expected_review)
            else:
                self.assertFalse(delivery.irg_tfm_review_id)
            self.assertEqual(delivery.irg_tfm_review_state, 'approved')
            self.assertEqual(delivery.irg_tfm_reviewed_at, review.reviewed_at)

        actor_orders = (
            ((self.internal_user, False), (self.reviewer, review)),
            ((self.reviewer, review), (self.internal_user, False)),
        )
        for first, second in actor_orders:
            with self.subTest(first=first[0].login, second=second[0].login):
                self.partial.invalidate_recordset(summary_fields)
                assert_summary(*first)
                assert_summary(*second)

    def test_create_rejects_all_client_review_metadata_values(self):
        forged_values = {
            'reviewed_by': (self.reviewer.id, False),
            'reviewed_at': (fields.Datetime.now(), False),
        }
        for actor in (self.internal_user, self.portal_user, self.reviewer):
            for field_name, values in forged_values.items():
                for value in values:
                    with self.subTest(actor=actor.login, field=field_name, value=value):
                        Review = self.env['irg.tfm.entrega.revision'].with_user(actor)
                        with self.assertRaises(AccessError):
                            Review.create({
                                'delivery_id': self.partial.id,
                                'state': 'approved',
                                field_name: value,
                            })

    def test_write_rejects_all_client_review_metadata_values(self):
        review = self._create_review(state='pending', comment=False)
        forged_values = {
            'reviewed_by': (self.reviewer.id, False),
            'reviewed_at': (fields.Datetime.now(), False),
        }
        for actor in (self.internal_user, self.portal_user, self.reviewer):
            for field_name, values in forged_values.items():
                for value in values:
                    with self.subTest(actor=actor.login, field=field_name, value=value):
                        with self.assertRaises(AccessError):
                            review.with_user(actor).write({field_name: value})

    def test_reserved_context_and_defaults_never_authorize_public_create_or_write(self):
        reserved = {
            '_irg_tfm_private_review': True,
            '_irg_tfm_review_actor_id': self.reviewer.id,
            'default_reviewed_by': self.reviewer.id,
            'default_reviewed_at': fields.Datetime.now(),
        }
        review = self._create_review(state='pending', comment=False)
        for actor in (self.internal_user, self.portal_user, self.reviewer):
            for key, value in reserved.items():
                with self.subTest(actor=actor.login, operation='create', key=key):
                    Review = self.env['irg.tfm.entrega.revision'].with_user(actor)
                    with self.assertRaises(AccessError):
                        Review.with_context(**{key: value}).create({
                            'delivery_id': self.partial.id,
                            'state': 'pending',
                        })
                with self.subTest(actor=actor.login, operation='write', key=key):
                    with self.assertRaises(AccessError):
                        review.with_user(actor).with_context(**{key: value}).write({
                            'comment': 'forged context',
                        })

    def test_pending_review_is_unstamped_until_server_publishes_decision(self):
        review = self._create_review(state='pending', comment=False)
        self.assertFalse(review.reviewed_by)
        self.assertFalse(review.reviewed_at)
        self.assertEqual(self.partial.irg_tfm_review_state, 'pending')

        review.write({'state': 'approved'})

        self.assertEqual(review.reviewed_by, self.reviewer)
        self.assertTrue(review.reviewed_at)
        self.assertEqual(self.partial.irg_tfm_review_state, 'approved')

    def test_open_action_creates_or_reuses_review_and_rejects_invalid_delivery(self):
        action = self.partial.with_user(self.reviewer).action_open_tfm_review()
        review = self.partial.irg_tfm_review_id
        self.assertTrue(review)
        self.assertEqual(action['res_model'], 'irg.tfm.entrega.revision')
        self.assertEqual(action['res_id'], review.id)
        self.assertEqual(
            self.partial.with_user(self.reviewer).action_open_tfm_review()['res_id'],
            review.id,
        )

        _owner, _student, _course, _enrollment, thesis = self._portal_case()
        outline = self._delivery(thesis, 'outline', 'outline-action.pdf')
        with self.assertRaises(ValidationError):
            outline.with_user(self.reviewer).action_open_tfm_review()

        self.thesis.write({'irg_tfm_activated_at': False})
        with self.assertRaises(ValidationError):
            self.partial.with_user(self.reviewer).action_open_tfm_review()


@tagged('post_install', '-at_install')
class TestTfmDeliveryReviewPortal(TfmFixtureMixin, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        helper = TfmFixtureMixin()
        helper.env = cls.env
        cls.owner_a, _student_a, cls.course_a, _enrollment_a, thesis_a = (
            helper._portal_case(login='tfm_review_portal_a')
        )
        cls.owner_b, _student_b, cls.course_b, _enrollment_b, thesis_b = (
            helper._portal_case(login='tfm_review_portal_b')
        )
        thesis_a.write({'irg_tfm_convocation_id': helper._convocation().id})
        thesis_b.write({'irg_tfm_convocation_id': helper._convocation().id})
        delivery_a = cls.env['irg.tfm.entrega']._irg_create_locked_submission(
            thesis_a,
            'partial',
            PDF_BYTES,
            'student-a.pdf',
            'application/pdf',
        )
        cls.env['irg.tfm.entrega']._irg_create_locked_submission(
            thesis_b,
            'partial',
            PDF_BYTES,
            'student-b.pdf',
            'application/pdf',
        )
        reviewer = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'TFM portal feedback reviewer',
            'login': 'tfm_review_portal_reviewer',
            'groups_id': [Command.set([
                cls.env.ref('irg_tfm_convocatorias.group_tfm_reviewer').id,
            ])],
        })
        cls.env['irg.tfm.entrega.revision'].with_user(reviewer).create({
            'delivery_id': delivery_a.id,
            'state': 'corrections',
            'comment': 'Corrige la metodología <script>alert("xss")</script>',
        })

    def test_only_owner_sees_escaped_readonly_feedback_for_exact_delivery(self):
        self.authenticate(self.owner_a.login, self.owner_a.login)
        page_a = self.url_open('/campus/course/%s/tfm' % self.course_a.id)

        self.assertEqual(page_a.status_code, 200)
        self.assertIn('Requiere correcciones', page_a.text)
        self.assertIn('Corrige la metodología', page_a.text)
        self.assertIn(
            '&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;',
            page_a.text,
        )
        self.assertNotIn('<script>alert("xss")</script>', page_a.text)
        self.assertNotRegex(page_a.text, r'name="(?:review_state|review_comment)"')

        self.authenticate(self.owner_b.login, self.owner_b.login)
        page_b = self.url_open('/campus/course/%s/tfm' % self.course_b.id)

        self.assertEqual(page_b.status_code, 200)
        self.assertNotIn('Corrige la metodología', page_b.text)
