# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError

class TestNlexGradeExemption(TransactionCase):

    def setUp(self):
        super(TestNlexGradeExemption, self).setUp()

        # Create a course
        self.course = self.env['op.course'].sudo().create({
            'name': 'Curso de Prueba NLEX',
            'code': 'CPNLEX01',
            'institute_key': '12345',
            'career_key': '67890',
            'rvoe_number': 'RVOE-111',
            'rvoe_date': '2020-01-01',
            'id_carrera': 'CARR-1',
            'calificacion_minima': 5,
            'calificacion_maxima': 10,
            'calificacion_minima_aprobatoria': 8,
        })

        # Create two subjects: one regular, one extra (NLEX)
        self.subject_regular = self.env['op.subject'].sudo().create({
            'name': 'Materia Regular',
            'code': 'MATREG01',
            'subject_type': 'compulsory',
            'credit_point': 5.0,
        })

        self.subject_nlex = self.env['op.subject'].sudo().create({
            'name': 'Materia Extra',
            'code': 'NLEX01',
            'subject_type': 'compulsory',
            'credit_point': 0.0,
        })

        self.course.sudo().write({
            'subject_ids': [(4, self.subject_regular.id), (4, self.subject_nlex.id)]
        })

        # Create a gradebook template with a line of 100% weight to satisfy validation constraints
        self.gradebook_template = self.env['app.gradebook'].sudo().create({
            'name': 'Plantilla de Calificaciones Test',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100,
                'qty': 1,
            })]
        })

        self.course.sudo().write({
            'gradebook_id': self.gradebook_template.id,
        })

        # Create student and partner
        self.partner = self.env['res.partner'].sudo().create({
            'name': 'Estudiante Test NLEX',
            'l10n_mx_edi_curp': 'AAAA000000AAAAAA00',
        })

        self.student = self.env['op.student'].sudo().create({
            'first_name': 'Estudiante',
            'last_name': 'Test NLEX',
            'gender': 'm',
            'partner_id': self.partner.id,
        })

        # Create admission register
        self.product = self.env['product.product'].sudo().create({
            'name': 'Servicio Academico',
            'type': 'service',
        })
        self.register = self.env['op.admission.register'].sudo().create({
            'name': 'Registro Test NLEX',
            'course_id': self.course.id,
            'product_id': self.product.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 10,
        })

        self.admission = self.env['op.admission'].sudo().create({
            'student_id': self.student.id,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_number': 'MAT-NLEX-999',
            'state': 'done',
            'name': 'Estudiante Test NLEX',
            'first_name': self.student.first_name,
            'last_name': self.student.last_name,
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'test@example.com',
            'is_student': True,
        })

        # Create batch
        self.batch = self.env['op.batch'].sudo().create({
            'name': 'Grupo Test NLEX',
            'code': 'GTNLEX01',
            'course_id': self.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })

        # Create student gradebook
        self.gradebook_student = self.env['app.gradebook.student'].sudo().create({
            'admission_id': self.admission.id,
            'state': 'in_progress',
        })

        # Create gradebook subjects
        self.gb_subject_regular = self.env['app.gradebook.subject'].sudo().create({
            'gradebook_student_id': self.gradebook_student.id,
            'op_subject_id': self.subject_regular.id,
        })

        self.gb_subject_nlex = self.env['app.gradebook.subject'].sudo().create({
            'gradebook_student_id': self.gradebook_student.id,
            'op_subject_id': self.subject_nlex.id,
        })

        # Set dec_responsable_id on company
        self.env.company.dec_responsable_id = self.partner.id

    def test_nlex_validation_and_calculations(self):
        """Test that NLEX subjects bypass state_to_done checks, are excluded from averages, and excluded from DEC export."""
        # 1. Without grades on both subjects, state_to_done should raise UserError because MATREG01 has no exam.
        with self.assertRaises(UserError):
            self.gradebook_student.state_to_done()

        # 2. Add an exam result to the regular subject, but leave NLEX subject without any grades.
        self.env['app.gradebook.result'].sudo().create({
            'gradebook_subject_id': self.gb_subject_regular.id,
            'survey_type': 'exam',
            'scoring_total': 9.0,
        })

        # Re-compute final subject notes
        self.gb_subject_regular.compute_final_subject_note()
        self.gb_subject_nlex.compute_final_subject_note()

        # Now, NLEX subject still has 0 exams (needs 1), but since its code starts with 'NLEX',
        # calling state_to_done should succeed without raising UserError!
        self.gradebook_student.state_to_done()
        self.assertEqual(self.gradebook_student.state, 'done', "Gradebook should be closed successfully.")

        # 3. Test average calculations:
        # regular final note: 9.0. NLEX final note: 0.0.
        # But average should ignore NLEX.
        self.gradebook_student._amount_prod_final()
        self.assertEqual(self.gradebook_student.total_final, 9.0, "Total final average should exclude NLEX subject.")

        self.gradebook_student.compute_avg_score()
        self.assertEqual(self.gradebook_student.avg_score, 9.0, "General average should exclude NLEX subject.")

        # 4. Test DEC export:
        dec_result_action = self.gradebook_student.action_export_to_dec()
        self.assertTrue(dec_result_action and dec_result_action.get('res_model') == 'dec.document')
        
        dec_document_ids = dec_result_action['context']['active_ids']
        dec_documents = self.env['dec.document'].sudo().browse(dec_document_ids)
        self.assertEqual(len(dec_documents), 1)
        dec_doc = dec_documents[0]

        # Total compulsory subjects in course (excluding NLEX) = 1 (MATREG01)
        self.assertEqual(dec_doc.total, 1, "DEC Document total subjects should exclude NLEX.")
        self.assertEqual(dec_doc.total_creditos, 5, "DEC Document total credits should exclude NLEX.")

        # Subject lines in dec document should only contain the regular subject
        self.assertEqual(len(dec_doc.asignaturas_line), 1, "DEC Document should have exactly 1 subject line.")
        self.assertEqual(dec_doc.asignaturas_line[0].clave_asignatura, 'MATREG01')
