# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields

class TestDiplomaGraduacion(TransactionCase):

    def setUp(self):
        super(TestDiplomaGraduacion, self).setUp()
        
        # 1. Create ResPartner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Student Partner',
        })
        
        # 2. Create OpStudent
        self.student = self.env['op.student'].create({
            'partner_id': self.partner.id,
            'first_name': 'Test',
            'last_name': 'Student',
        })
        
        # 3. Create OpCourse (include name_cat if available)
        course_vals = {
            'name': 'Máster de Prueba',
            'code': 'M-PRUEBA',
        }
        if 'name_cat' in self.env['op.course']._fields:
            course_vals['name_cat'] = 'Màster de Prova'
        self.course = self.env['op.course'].create(course_vals)
        
        # 4. Create OpBatch
        self.batch = self.env['op.batch'].create({
            'name': 'Test Batch',
            'code': 'B-TEST',
            'course_id': self.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })
        
        # 5. Create OpStudentCourse
        self.student_course = self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'roll_number': '123456',
        })

    def test_graduation_diploma_wizard_flow(self):
        # - Launches the wizard action on the student, gets the active action.
        action = self.student.action_open_graduation_diploma_wizard()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'irg.diploma.graduacion.wizard')
        
        # - Instantiates the wizard irg.diploma.graduacion.wizard passing student, course, and date
        wizard = self.env['irg.diploma.graduacion.wizard'].create({
            'student_id': self.student.id,
            'student_course_id': self.student_course.id,
            'date': fields.Date.today(),
        })
        
        # - Calls action_print_pdf() on the wizard
        res_action = wizard.action_print_pdf()
        
        # - Asserts that the return action is of type ir.actions.act_url
        self.assertEqual(res_action.get('type'), 'ir.actions.act_url')
        self.assertTrue(res_action.get('url'))
        
        # - Asserts that an ir.attachment is successfully created for res_model='op.student'
        #   and the student's ID, has a PDF mimetype, and contains valid binary data.
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.student'),
            ('res_id', '=', self.student.id),
            ('mimetype', '=', 'application/pdf'),
        ])
        self.assertTrue(attachment, "Attachment should be created")
        self.assertEqual(attachment.res_model, 'op.student')
        self.assertEqual(attachment.res_id, self.student.id)
        self.assertEqual(attachment.mimetype, 'application/pdf')
        self.assertTrue(attachment.datas, "Attachment datas must contain binary data")
