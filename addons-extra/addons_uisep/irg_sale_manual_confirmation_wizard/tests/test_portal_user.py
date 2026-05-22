# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestPortalUserSafeguard(TransactionCase):

    def setUp(self):
        super(TestPortalUserSafeguard, self).setUp()

        self.course = self.env['op.course'].create({
            'name': 'Test Course',
            'code': 'T-CR',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Course Product',
            'type': 'service',
        })

        self.register = self.env['op.admission.register'].create({
            'name': 'Test Register',
            'course_id': self.course.id,
            'period': '2026-05',
            'start_date': '2026-05-01',
            'end_date': '2026-06-30',
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })

        # Create a batch
        self.batch = self.env['op.batch'].create({
            'name': 'Test Batch',
            'code': 'TST-B-01',
            'course_id': self.course.id,
            'start_date': '2026-06-01',
            'end_date': '2026-12-31',
        })

        # Ensure a fees term exists
        self.fees_term = self.env['op.fees.terms'].search([], limit=1)
        if not self.fees_term:
            self.fees_term = self.env['op.fees.terms'].create({
                'name': 'Test Fees Term',
                'fees_terms': 'fixed_days',
            })

    def test_enroll_student_creates_portal_user_if_missing(self):
        """Test Case 1: Student exists but has no user.
        We verify that enroll_student() auto-creates a portal user and links it.
        """
        # Create partner
        partner = self.env['res.partner'].create({
            'name': 'Existing Partner Without User',
            'email': 'partner_no_user@example.com',
        })
        
        # Pre-create student linked to partner, but user_id is False
        student = self.env['op.student'].create({
            'name': partner.name,
            'first_name': 'Existing',
            'last_name': 'Partner Without User',
            'gender': 'o',
            'partner_id': partner.id,
            'email': partner.email,
            'birth_date': '2000-01-01',
            'user_id': False,
        })

        # Create admission linked to student
        admission = self.env['op.admission'].create({
            'name': partner.name,
            'first_name': 'Existing',
            'last_name': 'Partner Without User',
            'birth_date': '2000-01-01',
            'gender': 'o',
            'email': partner.email,
            'partner_id': partner.id,
            'student_id': student.id,
            'is_student': True,
            'batch_id': self.batch.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_date': '2026-05-15',
            'fees_term_id': self.fees_term.id,
        })

        # Verify initial conditions
        self.assertFalse(student.user_id)

        # Call enroll_student
        admission.enroll_student()

        # Verify portal user was created and linked
        self.assertTrue(student.user_id)
        user = student.user_id
        self.assertEqual(user.login, partner.email)
        self.assertEqual(user.partner_id, partner)
        
        # Verify user has portal group
        portal_group = self.env.ref('base.group_portal')
        self.assertIn(portal_group, user.groups_id)
        self.assertTrue(user.is_student)

    def test_enroll_student_links_existing_portal_user(self):
        """Test Case 2: User already exists for the partner.
        We verify that enroll_student() links the existing user to the student.
        """
        # Create partner
        partner = self.env['res.partner'].create({
            'name': 'Existing Partner With User',
            'email': 'partner_with_user@example.com',
        })
        
        # Create user linked to partner
        user = self.env['res.users'].create({
            'name': partner.name,
            'login': partner.email,
            'partner_id': partner.id,
            'company_id': self.env.company.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # Pre-create student linked to partner, but user_id is False
        student = self.env['op.student'].create({
            'name': partner.name,
            'first_name': 'Existing',
            'last_name': 'Partner With User',
            'gender': 'o',
            'partner_id': partner.id,
            'email': partner.email,
            'birth_date': '2000-01-01',
            'user_id': False,
        })

        # Create admission linked to student
        admission = self.env['op.admission'].create({
            'name': partner.name,
            'first_name': 'Existing',
            'last_name': 'Partner With User',
            'birth_date': '2000-01-01',
            'gender': 'o',
            'email': partner.email,
            'partner_id': partner.id,
            'student_id': student.id,
            'is_student': True,
            'batch_id': self.batch.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_date': '2026-05-15',
            'fees_term_id': self.fees_term.id,
        })

        # Verify initial state
        self.assertFalse(student.user_id)

        # Call enroll_student
        admission.enroll_student()

        # Verify student user_id has been linked to the existing user
        self.assertEqual(student.user_id, user)

    def test_enroll_student_handles_duplicate_login(self):
        """Test Case 3: User exists with the login/email, but linked to a different partner.
        We verify that it links the student to the existing user and updates student's partner
        to match user's partner to avoid duplicate user creation / crashes.
        """
        # Create partner A who has a user
        partner_a = self.env['res.partner'].create({
            'name': 'Partner A',
            'email': 'shared@example.com',
        })
        user_a = self.env['res.users'].create({
            'name': partner_a.name,
            'login': partner_a.email,
            'partner_id': partner_a.id,
            'company_id': self.env.company.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # Create partner B who doesn't have a user, but has the same email
        partner_b = self.env['res.partner'].create({
            'name': 'Partner B',
            'email': 'shared@example.com',
        })
        
        # Pre-create student for partner B, user_id is False
        student = self.env['op.student'].create({
            'name': partner_b.name,
            'first_name': 'Partner',
            'last_name': 'B',
            'gender': 'o',
            'partner_id': partner_b.id,
            'email': partner_b.email,
            'birth_date': '2000-01-01',
            'user_id': False,
        })

        # Create admission linked to student for partner B
        admission = self.env['op.admission'].create({
            'name': partner_b.name,
            'first_name': 'Partner',
            'last_name': 'B',
            'birth_date': '2000-01-01',
            'gender': 'o',
            'email': partner_b.email,
            'partner_id': partner_b.id,
            'student_id': student.id,
            'is_student': True,
            'batch_id': self.batch.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_date': '2026-05-15',
            'fees_term_id': self.fees_term.id,
        })

        # Call enroll_student
        admission.enroll_student()

        # Verify student was linked to user_a and student/admission partner switched to partner_a
        self.assertEqual(student.user_id, user_a)
        self.assertEqual(student.partner_id, partner_a)
        self.assertEqual(admission.partner_id, partner_a)
