# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestStudentResetPassword(TransactionCase):

    def setUp(self):
        super(TestStudentResetPassword, self).setUp()
        self.Partner = self.env['res.partner']
        self.User = self.env['res.users']
        self.Student = self.env['op.student']

        # Create a partner for the student
        self.partner_student = self.Partner.create({
            'name': 'Student Test',
            'email': 'student.test@example.com',
        })

        # Create a user for the student
        self.user_student = self.User.create({
            'name': 'Student Test User',
            'login': 'student.test@example.com',
            'partner_id': self.partner_student.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        # Create a student with a linked user
        self.student_with_user = self.Student.create({
            'name': 'Student Test',
            'first_name': 'Student',
            'last_name': 'Test',
            'partner_id': self.partner_student.id,
            'user_id': self.user_student.id,
            'email': 'student.test@example.com',
        })

        # Create another student without a user
        self.partner_student_no_user = self.Partner.create({
            'name': 'Student Test No User',
            'email': 'student.no_user@example.com',
        })
        self.student_no_user = self.Student.create({
            'name': 'Student Test No User',
            'first_name': 'Student',
            'last_name': 'No User',
            'partner_id': self.partner_student_no_user.id,
            'user_id': False,
            'email': 'student.no_user@example.com',
        })

    def test_01_action_generate_password_success(self):
        """ Test that generating a password for a student with a linked user succeeds """
        action = self.student_with_user.action_generate_password()

        # Check that the action details are correct
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'isep.generate.password.wizard')
        self.assertEqual(action.get('target'), 'new')

        # Check that the wizard record exists and contains the generated password
        wizard_id = action.get('res_id')
        wizard = self.env['isep.generate.password.wizard'].browse(wizard_id)
        self.assertTrue(wizard.exists())
        self.assertEqual(wizard.user_id, self.user_student)
        self.assertTrue(wizard.generated_password)

        # Check that the user's password was updated
        self.assertEqual(self.user_student.new_password_user, wizard.generated_password)

    def test_02_action_generate_password_no_user_fails(self):
        """ Test that generating a password for a student without a linked user fails with UserError """
        with self.assertRaises(UserError):
            self.student_no_user.action_generate_password()
