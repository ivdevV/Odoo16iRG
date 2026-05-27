# -*- coding: utf-8 -*-
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged
from odoo.addons.irg_online_subject_portal_visibility.controllers.main import OnlineSubjectVisibilitySlides


@tagged('post_install', '-at_install')
class TestOnlineSubjectPortalVisibility(TransactionCase):

    def setUp(self):
        super().setUp()
        
        # 1. Create subjects
        self.subject_a = self.env['op.subject'].create({
            'name': 'Test Portal Subject A',
            'code': 'IRG-TPS-A',
        })
        self.subject_b = self.env['op.subject'].create({
            'name': 'Test Portal Subject B',
            'code': 'IRG-TPS-B',
        })
        
        # Create Slide Channels and link them to subjects
        self.channel_a = self.env['slide.channel'].create({
            'name': 'Slide Channel A',
        })
        self.channel_b = self.env['slide.channel'].create({
            'name': 'Slide Channel B',
        })
        self.subject_a.write({'slide_channel_id': self.channel_a.id})
        self.subject_b.write({'slide_channel_id': self.channel_b.id})

        # 2. Create course and associate subjects
        self.course = self.env['op.course'].create({
            'name': 'Portal Test Course',
            'code': 'PTC',
            'subject_ids': [(6, 0, [self.subject_a.id, self.subject_b.id])],
        })

        # 3. Create register requirements
        self.product = self.env['product.product'].create({
            'name': 'Portal Fee',
            'type': 'service',
        })
        self.register = self.env['op.admission.register'].create({
            'name': 'Portal Register',
            'course_id': self.course.id,
            'product_id': self.product.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=120),
            'min_count': 1,
            'max_count': 30,
        })

        # 4. Create partner and student user
        self.partner = self.env['res.partner'].create({
            'name': 'Portal Test Student',
            'email': 'portal.student@example.com',
        })
        self.student_user = self.env['res.users'].create({
            'name': 'Portal Test Student',
            'login': 'portal_test_student',
            'email': 'portal.student@example.com',
            'partner_id': self.partner.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # Instantiate the controller
        self.controller = OnlineSubjectVisibilitySlides()

    def _create_batch(self, code, start_date=None, end_date=None):
        today = date.today()
        return self.env['op.batch'].create({
            'name': 'Test Batch %s' % code,
            'code': code,
            'course_id': self.course.id,
            'start_date': start_date or (today - timedelta(days=30)),
            'end_date': end_date or (today + timedelta(days=90)),
        })

    def _create_online_batch_no_dates(self, code):
        batch = self._create_batch(code)
        # Clear subject_to_batch_ids to enable individual online subject opening dates logic
        batch.subject_to_batch_ids.unlink()
        return batch

    def _create_admission(self, batch, partner=None, admission_date=None, due_date=None):
        today = date.today()
        partner = partner or self.partner
        return self.env['op.admission'].create({
            'first_name': 'Portal',
            'last_name': 'Student',
            'name': 'Portal Student',
            'birth_date': date(1990, 1, 1),
            'gender': 'o',
            'email': partner.email,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': batch.id,
            'admission_date': admission_date or today,
            'due_date': due_date,
            'partner_id': partner.id,
            'state': 'done',
        })

    def _get_mock_request(self):
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.student_user)
        mock_req.redirect = lambda url: f"redirect:{url}"
        return mock_req

    def test_active_online_student_access(self):
        """Test Case 1: Active online student.
        Create an online admission (using an online batch with no dates so it triggers irg_has_online_subject_opening_context())
        with today <= due_date, and verify they can access subjects when they are in their opening windows.
        """
        today = date.today()
        # Create active online admission (due_date in future)
        batch = self._create_online_batch_no_dates('MOPCONL')
        # Setting admission_date to today so the first subject is open from today
        admission = self._create_admission(batch, admission_date=today, due_date=today + timedelta(days=30))
        
        # Verify that irg_has_online_subject_opening_context() is True
        self.assertTrue(admission.irg_has_online_subject_opening_context())
        
        # Mock request and check visibility for subject_a (which opens today and ends in 29 days)
        mock_req = self._get_mock_request()
        with patch('odoo.addons.irg_online_subject_portal_visibility.controllers.main.request', mock_req):
            res_a = self.controller._check_subject_visibility(self.channel_a)
            # Access should be allowed (returns None)
            self.assertIsNone(res_a)

            # Access to subject_b should be blocked because it's not yet in the opening window (opens in 30 days)
            res_b = self.controller._check_subject_visibility(self.channel_b)
            self.assertEqual(res_b, f"redirect:/warning/subject-visibility/{self.channel_b.id}")

    def test_expired_online_student_blocked(self):
        """Test Case 2: Expired online student.
        Create an online admission with today > due_date, and verify they are redirected or blocked.
        """
        today = date.today()
        # Create expired online admission (due_date in the past)
        batch = self._create_online_batch_no_dates('MOPCONL')
        admission = self._create_admission(batch, admission_date=today - timedelta(days=10), due_date=today - timedelta(days=1))
        
        # Verify expired redirect
        mock_req = self._get_mock_request()
        with patch('odoo.addons.irg_online_subject_portal_visibility.controllers.main.request', mock_req):
            res_a = self.controller._check_subject_visibility(self.channel_a)
            # Expired student should be redirected to the expired warning page for online admission
            self.assertEqual(res_a, f"redirect:/warning/online_admission/{admission.id}")

    def test_mixed_admissions_access(self):
        """Test Case 3: Mixed admissions.
        Create two admissions for the same partner: one traditional batch admission which is expired
        (e.g. end_date is last year), and one online admission which is active (e.g. due_date is next year).
        Verify that when calling _check_subject_visibility for the online course channel, access is allowed
        (returns None) and not blocked by the expired traditional admission.
        """
        today = date.today()
        
        # 1. Expired traditional admission (last year)
        traditional_batch = self._create_batch(
            'TRADITIONAL_EXPIRED',
            start_date=today - timedelta(days=400),
            end_date=today - timedelta(days=365)
        )
        traditional_admission = self._create_admission(
            traditional_batch,
            admission_date=today - timedelta(days=400)
        )
        
        # 2. Active online admission (next year)
        online_batch = self._create_online_batch_no_dates('MOPCONL_ACTIVE')
        online_admission = self._create_admission(
            online_batch,
            admission_date=today,
            due_date=today + timedelta(days=365)
        )
        
        mock_req = self._get_mock_request()
        with patch('odoo.addons.irg_online_subject_portal_visibility.controllers.main.request', mock_req):
            res_a = self.controller._check_subject_visibility(self.channel_a)
            # Access should be allowed (returns None) due to the active online admission
            self.assertIsNone(res_a)

    def test_standard_admissions(self):
        """Test Case 4: Standard admissions.
        Verify visibility checks for traditional batch admissions (active vs expired).
        """
        today = date.today()
        
        # Create standard batch (active)
        active_batch = self._create_batch('TRAD_ACTIVE', start_date=today - timedelta(days=10), end_date=today + timedelta(days=30))
        active_admission = self._create_admission(active_batch, admission_date=today - timedelta(days=10))
        
        # By default, since batch_visibility_ids is not set, standard visible check is allowed
        mock_req = self._get_mock_request()
        with patch('odoo.addons.irg_online_subject_portal_visibility.controllers.main.request', mock_req):
            res_a = self.controller._check_subject_visibility(self.channel_a)
            self.assertIsNone(res_a)

        # Unlink the active admission to test expired batch
        active_admission.unlink()
        
        # Create expired standard batch
        expired_batch = self._create_batch('TRAD_EXPIRED', start_date=today - timedelta(days=40), end_date=today - timedelta(days=1))
        expired_admission = self._create_admission(expired_batch, admission_date=today - timedelta(days=40))
        
        with patch('odoo.addons.irg_online_subject_portal_visibility.controllers.main.request', mock_req):
            res_a = self.controller._check_subject_visibility(self.channel_a)
            # Access should be blocked
            self.assertEqual(res_a, f"redirect:/warning/subject-visibility/{self.channel_a.id}")

    def test_clone_redirection_preservation(self):
        """Test Case 5: Clone redirection preservation.
        Set self.channel_a.irg_online_channel_id = self.channel_b.id.
        Create an online active admission (using _create_online_batch_no_dates('MOPCONL_CLONE'))
        with today <= due_date.
        Verify that calling self.controller.channel(self.channel_a) redirects the student
        to the online clone channel: redirect:/slides/<self.channel_b.id>.
        """
        self.channel_a.irg_online_channel_id = self.channel_b.id

        today = date.today()
        # Create active online admission (due_date in future)
        batch = self._create_online_batch_no_dates('MOPCONL_CLONE')
        admission = self._create_admission(batch, admission_date=today, due_date=today + timedelta(days=30))

        # Mock request and check channel redirection
        mock_req = self._get_mock_request()
        SlideChannelClass = type(self.env['slide.channel'])
        with patch.object(SlideChannelClass, '_irg_is_online_student_for_channel', return_value=True), \
             patch('odoo.addons.irg_online_subject_portal_visibility.controllers.main.request', mock_req):
            res = self.controller.channel(self.channel_a)
            # Verify they are redirected to the online clone channel channel_b
            res_content = res.data.decode('utf-8') if hasattr(res, 'data') else res
            self.assertEqual(res_content, f"redirect:/slides/{self.channel_b.id}")

