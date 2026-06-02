# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase


class TestIrgCertificatePartial(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create student and course
        cls.partner = cls.env['res.partner'].create({'name': 'Test Student Partial'})
        cls.course = cls.env['op.course'].create({'name': 'Test Course Partial', 'code': 'TCP01'})
        cls.batch = cls.env['op.batch'].create({
            'name': 'Batch Partial',
            'code': 'BP',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })

        # Admissions
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product Partial',
            'type': 'service',
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'Test Register Partial',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.admission = cls.env['op.admission'].create({
            'name': 'ADM-TEST-PARTIAL',
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'register_id': cls.register.id,
            'gender': 'm',
            'first_name': 'Test',
            'last_name': 'Student',
        })

        # Gradebook template config
        cls.gradebook_tmpl = cls.env['app.gradebook'].create({
            'name': 'Gradebook Template Test',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'qty': 2,
                'weight': 100,
            })]
        })
        # Link template to course
        cls.course.write({'gradebook_id': cls.gradebook_tmpl.id})
        cls.tmpl_line = cls.gradebook_tmpl.gradebook_template_ids[0]

        # Gradebooks
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
        })

        # Subjects
        cls.subject_normal = cls.env['op.subject'].create({
            'name': 'Subject Compulsory A',
            'code': 'SCA',
            'course_id': cls.course.id,
            'subject_type': 'compulsory',
        })
        cls.subject_pending = cls.env['op.subject'].create({
            'name': 'Subject Compulsory B',
            'code': 'SCB',
            'course_id': cls.course.id,
            'subject_type': 'compulsory',
        })

        # Link subjects to student gradebook
        cls.gb_subj_a = cls.env['app.gradebook.subject'].create({
            'gradebook_student_id': cls.gradebook.id,
            'op_subject_id': cls.subject_normal.id,
        })
        cls.gb_subj_b = cls.env['app.gradebook.subject'].create({
            'gradebook_student_id': cls.gradebook.id,
            'op_subject_id': cls.subject_pending.id,
        })

        # Create results for Subject A (2 exams, so it's complete)
        cls.env['app.gradebook.result'].create({
            'gradebook_subject_id': cls.gb_subj_a.id,
            'survey_type': 'exam',
            'scoring_total': 8.5,
        })
        cls.env['app.gradebook.result'].create({
            'gradebook_subject_id': cls.gb_subj_a.id,
            'survey_type': 'exam',
            'scoring_total': 9.5,
        })
        # Force computation
        cls.gb_subj_a.compute_final_subject_note()
        cls.gb_subj_a.compute_point_average()

        # Create only 1 result for Subject B (2 exams required, so it's incomplete / pending)
        cls.env['app.gradebook.result'].create({
            'gradebook_subject_id': cls.gb_subj_b.id,
            'survey_type': 'exam',
            'scoring_total': 7.0,
        })
        # Force computation
        cls.gb_subj_b.compute_final_subject_note()
        cls.gb_subj_b.compute_point_average()

    def test_01_partial_gradebook_fill_template(self):
        """Check template filling logic for partial gradebooks."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'state': 'draft',
        })
        # Run template filling logic
        res_file = cert._fill_template()
        self.assertTrue(res_file)

    def test_02_partial_gradebook_all_pending_fill_template(self):
        """Check template filling logic when all compulsory subjects are pending."""
        # Unlink results for Subject A to make it pending too
        self.gb_subj_a.gradebook_result_ids.unlink()
        self.gb_subj_a.compute_final_subject_note()
        self.gb_subj_a.compute_point_average()

        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'state': 'draft',
        })
        res_file = cert._fill_template()
        self.assertTrue(res_file)
