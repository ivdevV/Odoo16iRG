# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestIrgCertificateAttendance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create student and course
        cls.partner = cls.env['res.partner'].create({'name': 'Test Student Attendance'})
        cls.course = cls.env['op.course'].create({'name': 'Test Course', 'code': 'TC01'})
        
        # Modality HomeClass
        cls.modality_hc = cls.env['irg.course.modality'].search([('code', '=', 'homeclass')], limit=1)
        if not cls.modality_hc:
            cls.modality_hc = cls.env['irg.course.modality'].create({
                'name': 'HomeClass',
                'code': 'homeclass',
            })
        
        
        # Batches
        cls.batch_normal = cls.env['op.batch'].create({
            'name': 'Batch Normal',
            'code': 'BN',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })
        cls.batch_hc = cls.env['op.batch'].create({
            'name': 'Batch HC',
            'code': 'HC',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })

        # Subjects
        cls.subject = cls.env['op.subject'].create({
            'name': 'Subject A',
            'code': 'SA',
            'course_id': cls.course.id,
        })

        # Sessions
        cls.session = cls.env['op.session'].create({
            'name': 'Session 1',
            'course_id': cls.course.id,
            'batch_id': cls.batch_hc.id,
            'subject_id': cls.subject.id,
            'start_datetime': fields.Datetime.now(),
            'end_datetime': fields.Datetime.now(),
            'faculty_id': cls.env['op.faculty'].create({
                'name': 'Faculty Test',
                'first_name': 'Faculty',
                'last_name': 'Test',
                'birth_date': fields.Date.today(),
                'gender': 'male',
            }).id,
        })

        # Admissions
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'Test Register',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.admission_normal = cls.env['op.admission'].create({
            'name': 'ADM-TEST-ATT-NORM',
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'register_id': cls.register.id,
            'batch_id': cls.batch_normal.id,
            'gender': 'm',
            'first_name': 'Test',
            'last_name': 'Student',
        })
        cls.admission_hc = cls.env['op.admission'].create({
            'name': 'ADM-TEST-ATT-HC',
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'register_id': cls.register.id,
            'batch_id': cls.batch_hc.id,
            'gender': 'm',
            'first_name': 'Test',
            'last_name': 'Student',
        })

        # Gradebooks
        cls.gradebook_normal = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'admission_id': cls.admission_normal.id,
        })
        cls.gradebook_hc = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'admission_id': cls.admission_hc.id,
        })

    def test_01_attendance_requires_session(self):
        """Creating an attendance request without a session must raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook_hc.id,
                'document_type': 'attendance',
                'certificate_type': 'digital',
                'state': 'draft',
            })

    def test_02_attendance_restricted_to_homeclass_or_hc_batch(self):
        """Attendance request on a normal course/batch without HomeClass must raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook_normal.id,
                'document_type': 'attendance',
                'session_id': self.session.id,
                'certificate_type': 'digital',
                'state': 'draft',
            })

    def test_03_attendance_allowed_on_hc_batch(self):
        """Attendance request is allowed on HC batch even if course has no modality."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook_hc.id,
            'document_type': 'attendance',
            'session_id': self.session.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        self.assertTrue(cert)

    def test_04_attendance_allowed_on_homeclass_modality(self):
        """Attendance request is allowed on normal batch if course has homeclass modality."""
        self.course.write({'irg_modality_ids': [(4, self.modality_hc.id)]})
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook_normal.id,
            'document_type': 'attendance',
            'session_id': self.session.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        self.assertTrue(cert)

    def test_05_attendance_fill_template(self):
        """Check template filling logic for attendance."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook_hc.id,
            'document_type': 'attendance',
            'session_id': self.session.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        # Mock _replace_in_paragraph to avoid real DocxDocument processing errors
        # or just let it run if the template is successfully copied.
        # Since templates were copied from base, it should load and fill successfully.
        res_file = cert._fill_template()
        self.assertTrue(res_file)
