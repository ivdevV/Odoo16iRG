# -*- coding: utf-8 -*-
###############################################################################
#
#    iRG Inc
#    Copyright (C) 2009-TODAY iRG Inc
#
###############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestQuizAutoScoring(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super(TestQuizAutoScoring, cls).setUpClass()
        
        # Crear categoría de cuestionario
        cls.category = cls.env['op.quiz.category'].create({
            'name': 'Test Category',
        })
        
        # Crear cuestionario de prueba
        cls.quiz = cls.env['op.quiz'].create({
            'name': 'Test Quiz',
            'categ_id': cls.category.id,
            'state': 'draft',
            'assigned_to': 'open_for_all',
        })
        
        # Crear preguntas sin puntaje
        for i in range(5):
            cls.env['op.quiz.line'].create({
                'name': f'Question {i+1}',
                'answer': f'Answer {i+1}',
                'quiz_id': cls.quiz.id,
                'mark': 0.0,
            })
    
    def test_01_auto_score_distributes_marks_equally(self):
        """
        TC1: Distribución de puntajes
        Verifica que 100 puntos se distribuyan equitativamente entre preguntas.
        """
        # Ejecutar auto-scoring
        self.quiz.action_auto_score_quiz()
        
        # Verificar que cada pregunta tiene 20 puntos (100/5)
        expected_mark = 100.0 / len(self.quiz.line_ids)
        for line in self.quiz.line_ids:
            if not line.display_type:
                self.assertAlmostEqual(
                    line.mark, 
                    expected_mark, 
                    places=2,
                    msg=f"Pregunta {line.name} no tiene el puntaje correcto"
                )
    
    def test_02_auto_score_rejects_already_marked_quiz(self):
        """
        TC2: Rechazo si ya tiene puntajes
        Verifica que rechace cuestionarios que ya tienen puntajes.
        """
        # Crear un cuestionario con puntajes ya asignados
        quiz_with_marks = self.env['op.quiz'].create({
            'name': 'Quiz with Marks',
            'categ_id': self.category.id,
            'state': 'draft',
            'assigned_to': 'open_for_all',
        })
        
        # Agregar preguntas CON puntaje
        self.env['op.quiz.line'].create({
            'name': 'Question with mark',
            'answer': 'Answer',
            'quiz_id': quiz_with_marks.id,
            'mark': 25.0,  # Ya tiene puntaje
        })
        
        # Intentar ejecutar auto-scoring debe fallar
        with self.assertRaises(ValidationError):
            quiz_with_marks.action_auto_score_quiz()
    
    def test_03_auto_score_rejects_invalid_states(self):
        """
        TC3: Validación de estados válidos
        Verifica que solo funcione en Draft e In-Progress.
        """
        # Cambiar estado a 'done'
        self.quiz.write({'state': 'done'})
        
        # Intentar ejecutar debe fallar
        with self.assertRaises(ValidationError):
            self.quiz.action_auto_score_quiz()
    
    def test_04_auto_score_rejects_empty_quiz(self):
        """
        TC4: Validación de cuestionario vacío
        Verifica que rechace cuestionarios sin preguntas.
        """
        empty_quiz = self.env['op.quiz'].create({
            'name': 'Empty Quiz',
            'categ_id': self.category.id,
            'state': 'draft',
            'assigned_to': 'open_for_all',
        })
        
        # Intentar ejecutar debe fallar
        with self.assertRaises(ValidationError):
            empty_quiz.action_auto_score_quiz()
    
    def test_05_calculate_result_with_correct_answers(self):
        """
        TC5: Cálculo de puntajes en intentos correctos
        Verifica que calcula correctamente cuando las respuestas son correctas.
        """
        # Preparar quiz con puntajes
        self.quiz.action_auto_score_quiz()
        expected_mark_per_q = 100.0 / len(self.quiz.line_ids)
        
        # Crear un estudiante
        student = self.env['op.student'].create({
            'name': 'Test Student',
        })
        
        # Crear resultado (intento)
        result = self.env['op.quiz.result'].create({
            'quiz_id': self.quiz.id,
            'student_id': student.id,
        })
        
        # Crear líneas de resultado con respuestas CORRECTAS
        for line in self.quiz.line_ids:
            if not line.display_type:
                self.env['op.quiz.result.line'].create({
                    'result_id': result.id,
                    'line_id': line.id,
                    'answer': line.answer,
                    'given_answer': line.answer,  # Respuesta correcta
                    'name': line.name,
                    'mark': 0.0,  # Será calculado por el método
                })
        
        # Recalcular puntaje
        result.recalculate_score()
        
        # El puntaje total debe ser 100 (5 preguntas * 20 puntos)
        expected_total = expected_mark_per_q * len(self.quiz.line_ids)
        self.assertAlmostEqual(
            result.obtain_mark,
            expected_total,
            places=2,
            msg="El puntaje total no es correcto para respuestas correctas"
        )
    
    def test_06_calculate_result_with_wrong_answers(self):
        """
        TC6: Cálculo de puntajes en intentos incorrectos
        Verifica que calcula correctamente cuando las respuestas son incorrectas.
        """
        # Preparar quiz con puntajes
        self.quiz.action_auto_score_quiz()
        
        # Crear un estudiante
        student = self.env['op.student'].create({
            'name': 'Test Student 2',
        })
        
        # Crear resultado (intento)
        result = self.env['op.quiz.result'].create({
            'quiz_id': self.quiz.id,
            'student_id': student.id,
        })
        
        # Crear líneas de resultado con respuestas INCORRECTAS
        for line in self.quiz.line_ids:
            if not line.display_type:
                self.env['op.quiz.result.line'].create({
                    'result_id': result.id,
                    'line_id': line.id,
                    'answer': line.answer,
                    'given_answer': 'Wrong Answer',  # Respuesta incorrecta
                    'name': line.name,
                    'mark': 0.0,
                })
        
        # Recalcular puntaje
        result.recalculate_score()
        
        # El puntaje total debe ser 0
        self.assertEqual(
            result.obtain_mark,
            0.0,
            msg="El puntaje total debe ser 0 para respuestas incorrectas"
        )
    
    def test_07_mixed_correct_wrong_answers(self):
        """
        TC7: Cálculo con respuestas mixtas
        Verifica correcta combinación de respuestas correctas e incorrectas.
        """
        # Preparar quiz con puntajes
        self.quiz.action_auto_score_quiz()
        expected_mark_per_q = 100.0 / len(self.quiz.line_ids)
        
        # Crear un estudiante
        student = self.env['op.student'].create({
            'name': 'Test Student 3',
        })
        
        # Crear resultado
        result = self.env['op.quiz.result'].create({
            'quiz_id': self.quiz.id,
            'student_id': student.id,
        })
        
        # Crear líneas: 3 correctas, 2 incorrectas
        correct_count = 0
        for line in self.quiz.line_ids:
            if not line.display_type:
                is_correct = correct_count < 3
                correct_count += 1
                
                self.env['op.quiz.result.line'].create({
                    'result_id': result.id,
                    'line_id': line.id,
                    'answer': line.answer,
                    'given_answer': line.answer if is_correct else 'Wrong',
                    'name': line.name,
                    'mark': 0.0,
                })
        
        # Recalcular
        result.recalculate_score()
        
        # Puntaje esperado: 3 preguntas * 20 puntos = 60
        expected = 3 * expected_mark_per_q
        self.assertAlmostEqual(
            result.obtain_mark,
            expected,
            places=2,
            msg="Puntaje incorrecto con respuestas mixtas"
        )
