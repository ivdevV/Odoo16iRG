# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields


class TestActaGeneration(TransactionCase):
    """Pruebas de generación de actas de TFM/TFG."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Crear datos de prueba
        cls.student = cls.env['op.student'].create({
            'name': 'Juan García López',
            'identification_id': '12345678A',
        })

    def test_wizard_create_tfm_acta(self):
        """TC-001: Crear acta TFM básica desde el wizard."""
        wizard_data = {
            'student_id': self.student.id,
            'acta_type': 'tfm',
            'academic_year': '2025-2026',
            'degree_name': 'Máster Universitario en Psicología Clínica',
            'tfm_title': 'Efectividad de la terapia cognitivo-conductual en el tratamiento de la ansiedad',
            'director_name': 'María',
            'director_surnames': 'González Rodríguez',
            'president_name': 'Carlos',
            'president_surnames': 'López Martínez',
            'secretary_name': 'Santiago',
            'secretary_surnames': 'Borges Rodríguez',
            'defense_date': fields.Date.today(),
        }
        
        wizard = self.env['irg.tfm.acta.wizard'].create(wizard_data)
        
        # Generar PDF
        result = wizard.action_generate_acta_pdf()
        
        # Verificar que se retorna una acción de descarga
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'ir.actions.act_url')
        
        # Verificar que se creó el registro de acta
        acta = self.env['irg.tfm.acta'].search([('student_id', '=', self.student.id)])
        self.assertEqual(len(acta), 1)
        self.assertEqual(acta.acta_type, 'tfm')
        self.assertEqual(acta.state, 'valid')
        self.assertIsNotNone(acta.attachment_id)

    def test_wizard_create_tfg_acta(self):
        """TC-002: Crear acta TFG."""
        wizard_data = {
            'student_id': self.student.id,
            'acta_type': 'tfg',
            'academic_year': '2025-2026',
            'degree_name': 'Grado en Psicología',
            'tfm_title': 'Análisis de factores predictivos en el rendimiento académico',
            'director_name': 'Elena',
            'director_surnames': 'Martínez Fernández',
            'president_name': 'Roberto',
            'president_surnames': 'Sanchez García',
            'secretary_name': 'Santiago',
            'secretary_surnames': 'Borges Rodríguez',
            'defense_date': fields.Date.today(),
        }
        
        wizard = self.env['irg.tfm.acta.wizard'].create(wizard_data)
        result = wizard.action_generate_acta_pdf()
        
        self.assertIsNotNone(result)
        
        acta = self.env['irg.tfm.acta'].search([('student_id', '=', self.student.id)])
        self.assertEqual(len(acta), 1)
        self.assertEqual(acta.acta_type, 'tfg')

    def test_acta_pdf_download(self):
        """TC-004: Auditoría y descarga de PDF."""
        # Crear acta
        wizard_data = {
            'student_id': self.student.id,
            'acta_type': 'tfm',
            'academic_year': '2025-2026',
            'degree_name': 'Máster Universitario en Psicología',
            'tfm_title': 'Test Title',
            'director_name': 'Test',
            'director_surnames': 'Director',
            'president_name': 'Test',
            'president_surnames': 'President',
            'secretary_name': 'Test',
            'secretary_surnames': 'Secretary',
            'defense_date': fields.Date.today(),
        }
        
        wizard = self.env['irg.tfm.acta.wizard'].create(wizard_data)
        wizard.action_generate_acta_pdf()
        
        # Buscar acta y verificar descarga
        acta = self.env['irg.tfm.acta'].search([('student_id', '=', self.student.id)])
        result = acta.action_download_pdf()
        
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertIn('download=true', result['url'])

    def test_acta_name_computation(self):
        """Verificar que el nombre del acta se computa correctamente."""
        wizard_data = {
            'student_id': self.student.id,
            'acta_type': 'tfm',
            'academic_year': '2025-2026',
            'degree_name': 'Máster',
            'tfm_title': 'Test',
            'director_name': 'Test',
            'director_surnames': 'Test',
            'president_name': 'Test',
            'president_surnames': 'Test',
            'secretary_name': 'Test',
            'secretary_surnames': 'Test',
            'defense_date': fields.Date.today(),
        }
        
        wizard = self.env['irg.tfm.acta.wizard'].create(wizard_data)
        wizard.action_generate_acta_pdf()
        
        acta = self.env['irg.tfm.acta'].search([('student_id', '=', self.student.id)])
        self.assertIn('Juan', acta.name)
        self.assertIn('García', acta.name)
        self.assertIn('TFM', acta.name)
