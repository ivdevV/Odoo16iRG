# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class TestWelcomeMailSafeguard(TransactionCase):

    def setUp(self):
        super(TestWelcomeMailSafeguard, self).setUp()

        # Create a course
        self.course = self.env['op.course'].create({
            'name': 'Test Course',
            'code': 'T-CR',
        })

        # Create an online modality
        self.modality_online = self.env['op.modality'].create({
            'name': 'Online Modality',
            'code': 'MOD-ONL',
            'new_code': 'MOD-ONL',
            'analytic_code': 'MOD-ONL',
        })

        # Create a tutor user
        self.tutor_user = self.env['res.users'].create({
            'name': 'Test Tutor User',
            'login': 'test_tutor_user@example.com',
            'email': 'test_tutor_user@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        # Create a service product for course fees
        self.product = self.env['product.product'].create({
            'name': 'Test Course Product',
            'type': 'service',
        })

        # Create an admission register
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

    def test_send_mail_online_modality_auto_populates_date_start_class(self):
        """Test Case 1: Online batch by modality name, date_start_class is empty"""
        # Create a batch with no 'ONL' in code or name, but with online modality
        batch_regular = self.env['op.batch'].create({
            'name': 'Test Batch Regular',
            'code': 'REG-B-01',
            'course_id': self.course.id,
            'modality_id': self.modality_online.id,
            'start_date': '2026-06-01',
            'end_date': '2026-12-31',
            'date_start_class': False,  # Should remain False since it is not named 'ONL'
            'tutor_id': self.tutor_user.id,
        })

        # Verify that date_start_class is indeed False/empty initially
        self.assertFalse(batch_regular.date_start_class)

        # Create partner and admission
        partner = self.env['res.partner'].create({
            'name': 'Test Student 1',
            'email': 'student1@example.com',
        })
        admission = self.env['op.admission'].create({
            'name': 'Test Student 1',
            'first_name': 'Test',
            'last_name': 'Student 1',
            'birth_date': '2000-01-01',
            'gender': 'o',
            'email': 'student1@example.com',
            'partner_id': partner.id,
            'batch_id': batch_regular.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_date': '2026-05-15',
            'email_send_ok': False,
        })

        # Send welcome mail - should trigger auto-population of date_start_class
        res = admission.send_mail(force=False)
        self.assertTrue(res)
        self.assertTrue(admission.email_send_ok)

        # Verify the batch's date_start_class got auto-populated with start_date
        self.assertEqual(batch_regular.date_start_class, batch_regular.start_date)

    def test_send_mail_online_code_auto_populates_date_start_class(self):
        """Test Case 2: Online batch by code ('ONL' in code), date_start_class manually cleared"""
        # Create a batch with 'ONL' in its code
        batch_onl = self.env['op.batch'].create({
            'name': 'Test Batch ONL',
            'code': 'ONL-B-01',
            'course_id': self.course.id,
            'start_date': '2026-06-01',
            'end_date': '2026-12-31',
            'tutor_id': self.tutor_user.id,
        })

        # Force clear the date_start_class using SQL to bypass the default create/write hook of irg_openeducat_sale_lote_custom
        self.env.cr.execute("UPDATE op_batch SET date_start_class = NULL WHERE id = %s", [batch_onl.id])
        batch_onl.invalidate_recordset(['date_start_class'])

        # Verify it has been cleared
        self.assertFalse(batch_onl.date_start_class)

        # Create partner and admission
        partner = self.env['res.partner'].create({
            'name': 'Test Student 2',
            'email': 'student2@example.com',
        })
        admission = self.env['op.admission'].create({
            'name': 'Test Student 2',
            'first_name': 'Test',
            'last_name': 'Student 2',
            'birth_date': '2000-01-01',
            'gender': 'o',
            'email': 'student2@example.com',
            'partner_id': partner.id,
            'batch_id': batch_onl.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_date': '2026-05-15',
            'email_send_ok': False,
        })

        # Send welcome mail - should trigger auto-population of date_start_class
        res = admission.send_mail(force=False)
        self.assertTrue(res)
        self.assertTrue(admission.email_send_ok)

        # Verify the batch's date_start_class got auto-populated with start_date
        self.assertEqual(batch_onl.date_start_class, batch_onl.start_date)
