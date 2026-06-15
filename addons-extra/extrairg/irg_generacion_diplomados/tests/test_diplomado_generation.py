# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields

class TestDiplomadoGeneration(TransactionCase):

    def setUp(self):
        super(TestDiplomadoGeneration, self).setUp()
        
        # 1. Crear asignaturas con diferente modalidad
        self.sub_presencial = self.env['op.subject'].create({
            'name': 'Taller de Grafología Práctica',
            'code': 'GRAF_PRES',
            'irg_modality': 'presencial',
            'type': 'theory',
        })
        
        self.sub_online = self.env['op.subject'].create({
            'name': 'Introducción a la Psicología del Rostro',
            'code': 'PSIC_ONL',
            'irg_modality': 'online',
            'type': 'theory',
        })
        
        # 2. Crear un curso y asociarle las asignaturas
        self.course = self.env['op.course'].create({
            'name': 'Diplomado en Grafología y Morfopsicología',
            'code': 'DIP_GM',
            'subject_ids': [(6, 0, [self.sub_presencial.id, self.sub_online.id])],
        })
        
        # 3. Crear lote (batch) del curso
        self.batch = self.env['op.batch'].create({
            'name': 'Promoción 2026',
            'code': 'PROM_2026',
            'start_date': '2026-01-10',
            'end_date': '2026-06-10',
            'course_id': self.course.id,
        })
        
        # 4. Crear un partner y un estudiante
        self.partner = self.env['res.partner'].create({
            'name': 'Adrián López Test'
        })
        self.student = self.env['op.student'].create({
            'first_name': 'Adrián',
            'last_name': 'López Test',
            'partner_id': self.partner.id,
        })
        
        # 5. Configurar el layout de la compañía para evitar la redirección en report_action
        self.env.company.external_report_layout_id = self.env.ref("web.external_layout_standard").id

    def test_01_can_generate_diplomado_computation(self):
        """Probar que el campo can_generate_diplomado se calcula correctamente."""
        # Inicialmente no debe poder generar diplomados al no tener cursos
        self.student._compute_can_generate_diplomado()
        self.assertFalse(self.student.can_generate_diplomado, "El estudiante no debería poder generar diplomados sin cursos finalizados.")
        
        # Crear un curso inscrito en estado 'running'
        student_course = self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'state': 'running',
        })
        self.student._compute_can_generate_diplomado()
        self.assertFalse(self.student.can_generate_diplomado, "El estudiante no debería poder generar si el curso está 'running'.")
        
        # Cambiar a 'finished'
        student_course.write({'state': 'finished'})
        self.student._compute_can_generate_diplomado()
        self.assertTrue(self.student.can_generate_diplomado, "El estudiante debería poder generar diplomados con curso 'finished'.")

    def test_02_wizard_defaults_and_onchange(self):
        """Probar que el wizard carga correctamente los datos por defecto del alumno y curso."""
        # Registrar el curso finalizado para el alumno
        self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'state': 'finished',
        })
        
        # Crear wizard
        wizard = self.env['irg.diplomado.wizard'].with_context(default_student_id=self.student.id).create({
            'student_id': self.student.id,
        })
        
        # Simular onchange del estudiante
        wizard._onchange_student_id()
        self.assertEqual(wizard.student_name, self.student.name)
        self.assertEqual(wizard.course_id.id, self.course.id)
        self.assertEqual(wizard.start_date, self.batch.start_date)
        self.assertEqual(wizard.end_date, self.batch.end_date)
        
        # Simular onchange del curso
        wizard._onchange_course_id()
        self.assertEqual(wizard.diplomado_name, self.course.name)
        self.assertEqual(len(wizard.subject_ids), 2, "Deberían precargarse las 2 asignaturas del curso.")

    def test_03_registry_generation_and_report_action(self):
        """Probar que al confirmar el wizard se crea el registro del diplomado y se lanza el reporte."""
        self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'state': 'finished',
        })
        
        # Instanciar wizard con campos definidos
        wizard = self.env['irg.diplomado.wizard'].create({
            'student_id': self.student.id,
            'student_name': 'Adrián López Test Modificado',
            'course_id': self.course.id,
            'diplomado_name': 'Diplomado en Grafología Superior',
            'start_date': '2026-02-01',
            'end_date': '2026-05-30',
            'duration_hours': 150,
            'duration_ects': 6.0,
            'issue_date': fields.Date.today(),
            'diploma_type': 'digital',
            'subject_ids': [(6, 0, [self.sub_presencial.id, self.sub_online.id])]
        })
        
        action = wizard.action_print_diplomado()
        
        # Comprobar retorno de acción de reporte
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_name'], 'irg_generacion_diplomados.report_diplomado_template')
        
        # Buscar si el registro en la base de datos se creó
        registry = self.env['irg.diplomado.registry'].search([('student_id', '=', self.student.id)])
        self.assertEqual(len(registry), 1)
        self.assertEqual(registry.student_name, 'Adrián López Test Modificado')
        self.assertEqual(registry.diplomado_name, 'Diplomado en Grafología Superior')
        self.assertEqual(registry.duration_hours, 150)
        self.assertEqual(registry.duration_ects, 6.0)
        self.assertEqual(registry.start_date, fields.Date.from_string('2026-02-01'))
        self.assertEqual(registry.end_date, fields.Date.from_string('2026-05-30'))
        self.assertEqual(len(registry.subject_ids), 2)
        
        # Probar el método de reimpresión del registro
        reprint_action = registry.action_reprint()
        self.assertEqual(reprint_action['type'], 'ir.actions.report')
