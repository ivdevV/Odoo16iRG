# -*- coding: utf-8 -*-

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAcademicRequestPhase2(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Alumno Fase 2'})
        cls.student = cls.env['op.student'].create({
            'name': 'Alumno Fase 2',
            'partner_id': cls.partner.id,
        })
        cls.course = cls.env['op.course'].create({'name': 'Master Fase 2', 'code': 'MF2'})
        cls.batch = cls.env['op.batch'].create({
            'name': 'Batch Fase 2',
            'code': 'BF2',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'Registro Fase 2',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
        })
        cls.admission = cls.env['op.admission'].create({
            'name': 'ADM-F2',
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'register_id': cls.register.id,
            'gender': 'm',
            'first_name': 'Alumno',
            'last_name': 'Fase 2',
            'email': 'fase2@example.com',
            'birth_date': '1990-01-01',
        })
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'student_id': cls.student.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
            'state': 'done',
        })

    def test_portal_final_certificate_requires_paid_master(self):
        with self.assertRaises(ValidationError):
            self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'document_type': 'gradebook',
                'certificate_type': 'digital',
                'origin': 'portal',
                'state': 'pending_payment',
            })

    def test_partial_certificate_can_be_checked_without_full_master_payment(self):
        request = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'origin': 'portal',
            'state': 'pending_payment',
        })
        self.assertEqual(request.academic_payment_validation_state, 'eligible')
