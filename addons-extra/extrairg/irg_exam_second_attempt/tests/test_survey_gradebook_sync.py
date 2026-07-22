# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_sync_test')
class TestSurveyGradebookSync(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Estudiante Test Sync',
            'email': 'estudiante_sync@test.com',
        })

        cls.course = cls.env['op.course'].create({
            'name': 'Curso Test Sync',
            'code': 'CTS01',
        })

        cls.register = cls.env['op.admission.register'].create({
            'name': 'Registro Test Sync',
            'course_id': cls.course.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
        })

        cls.op_subject = cls.env['op.subject'].create({
            'name': 'Asignatura Test Sync',
            'code': 'ATS01',
            'course_id': cls.course.id,
            'subject_type': 'compulsory',
        })

        cls.admission = cls.env['op.admission'].create({
            'name': 'ADM-SYNC-001',
            'application_number': 'APP-SYNC-001',
            'first_name': 'Estudiante',
            'last_name': 'Sync',
            'partner_id': cls.partner.id,
            'email': 'estudiante_sync@test.com',
            'gender': 'm',
            'birth_date': '1995-01-01',
            'course_id': cls.course.id,
            'register_id': cls.register.id,
        })

        cls.channel = cls.env['slide.channel'].create({
            'name': 'Canal Test Sync',
        })

        cls.channel_partner = cls.env['slide.channel.partner'].create({
            'channel_id': cls.channel.id,
            'partner_id': cls.partner.id,
            'admission_id': cls.admission.id,
            'op_subject_id': cls.op_subject.id,
            'course_id': cls.course.id,
        })

        cls.survey_survey_type = cls.env['survey.survey'].create({
            'title': 'Cuestionario Evaluativo Test (survey_type=survey)',
            'survey_type': 'survey',
            'scoring_type': 'scoring_without_answers',
            'scoring_success_min': 70.0,
        })

        cls.slide = cls.env['slide.slide'].create({
            'name': 'Slide Cuestionario Test',
            'channel_id': cls.channel.id,
            'slide_category': 'document',
            'survey_id': cls.survey_survey_type.id,
        })

    def test_sync_survey_type_survey_to_gradebook(self):
        """Verifica que un intento tipo 'survey' completado cree el resultado en la libreta."""
        slide_partner = self.env['slide.slide.partner'].create({
            'slide_id': self.slide.id,
            'partner_id': self.partner.id,
        })

        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey_survey_type.id,
            'partner_id': self.partner.id,
            'slide_partner_id': slide_partner.id,
            'slide_id': self.slide.id,
        })

        self.assertFalse(user_input.result_id)

        # Simular finalizacion con nota del 85%
        user_input.write({
            'state': 'done',
            'scoring_percentage': 85.0,
        })

        self.assertTrue(user_input.result_id, "El intento tipo 'survey' debe crear result_id en libreta")
        self.assertEqual(user_input.result_id.scoring_total, 8.5)

    def test_action_sync_pending_survey_gradebooks_bulk(self):
        """Verifica que la accion masiva de regularizacion sincronice intentos pendientes sin result_id."""
        slide_partner = self.env['slide.slide.partner'].create({
            'slide_id': self.slide.id,
            'partner_id': self.partner.id,
        })

        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey_survey_type.id,
            'partner_id': self.partner.id,
            'slide_partner_id': slide_partner.id,
            'slide_id': self.slide.id,
        })

        # Forzar estado 'done' omitiendo el sync para simular registros historicos
        user_input.with_context(irg_skip_gradebook_sync=True).write({
            'state': 'done',
            'scoring_percentage': 90.0,
        })

        self.assertFalse(user_input.result_id)

        count = self.env['survey.user_input'].action_sync_pending_survey_gradebooks()
        self.assertGreaterEqual(count, 1)

        user_input.invalidate_recordset(['result_id'])
        self.assertTrue(user_input.result_id, "La regularizacion masiva debe asociar el result_id")
        self.assertEqual(user_input.result_id.scoring_total, 9.0)
