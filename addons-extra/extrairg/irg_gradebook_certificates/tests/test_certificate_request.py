# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestIrgCertificateRequest(TransactionCase):
    """Basic integration tests for irg.certificate.request."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create minimal linked records
        cls.partner = cls.env['res.partner'].create({'name': 'Test Student Portal'})
        cls.course = cls.env['op.course'].create({'name': 'Test Course', 'code': 'TC01'})
        cls.batch = cls.env['op.batch'].create({
            'name': 'Batch A', 'code': 'BA', 'course_id': cls.course.id
        })
        cls.admission = cls.env['op.admission'].create({
            'name': 'ADM-TEST',
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
        })
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
        })

    # ------------------------------------------------------------------
    # Sequence
    # ------------------------------------------------------------------

    def test_01_sequence_assigned_on_create(self):
        """name should be populated from ir.sequence, not stay 'New'."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        self.assertNotEqual(cert.name, 'New', 'Sequence was not assigned on create.')
        self.assertTrue(cert.name.startswith('CERT/'), 'Sequence prefix mismatch.')

    # ------------------------------------------------------------------
    # Price computation
    # ------------------------------------------------------------------

    def test_02_digital_price_no_shipping(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        self.assertAlmostEqual(cert.price_base, 30.0)
        self.assertAlmostEqual(cert.price_shipping, 0.0)
        self.assertAlmostEqual(cert.price_total, 30.0)

    def test_03_physical_national_price(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'physical',
            'shipping_type': 'national',
            'state': 'draft',
        })
        self.assertAlmostEqual(cert.price_base, 40.0)
        self.assertAlmostEqual(cert.price_shipping, 20.0)
        self.assertAlmostEqual(cert.price_total, 60.0)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    def test_04_physical_without_shipping_raises(self):
        with self.assertRaises(ValidationError):
            self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'certificate_type': 'physical',
                # shipping_type intentionally omitted
                'state': 'draft',
            })

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def test_05_cancel_draft(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        cert.action_cancel()
        self.assertEqual(cert.state, 'cancelled')

    def test_06_cannot_cancel_done(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'done',
        })
        with self.assertRaises(UserError):
            cert.action_cancel()

    def test_07_process_payment_physical(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'physical',
            'shipping_type': 'national',
            'state': 'pending_payment',
        })
        cert._process_payment()
        self.assertEqual(cert.state, 'paid', 'Physical cert should be in "paid" after payment.')

    # ------------------------------------------------------------------
    # app.gradebook.student inherit
    # ------------------------------------------------------------------

    def test_08_certificate_count(self):
        initial_count = self.gradebook.certificate_count
        self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'done',
        })
        self.gradebook.invalidate_recordset(['certificate_count'])
        self.assertEqual(self.gradebook.certificate_count, initial_count + 1)
