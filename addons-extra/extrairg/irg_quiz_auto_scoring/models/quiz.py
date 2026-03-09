# -*- coding: utf-8 -*-
###############################################################################
#
#    iRG Inc
#    Copyright (C) 2009-TODAY iRG Inc
#
###############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpQuiz(models.Model):
    _inherit = "op.quiz"

    # Field to indicate LMS integration / visibility toggle
    lms = fields.Boolean(string="LMS", default=False)

    def action_auto_score_quiz(self):
        """
        Acción para auto-calcular y asignar puntajes automáticamente.
        
        1. Si NO todas las preguntas tienen puntaje:
           - Divide 100 entre el número de preguntas con puntaje 0/None
           - Asigna ese puntaje a cada pregunta
           
        2. Procesa TODOS los resultados existentes (intentos de estudiantes):
           - Para cada respuesta correcta: asigna el puntaje de la pregunta
           - Para cada respuesta incorrecta: asigna 0
           - Recalcula el total de puntaje del resultado
           
        3. Si openeducat_grading está instalado:
           - Sincroniza con el boletín de calificaciones
        """
        self.ensure_one()
        
        # Validar estado
        if self.state not in ['draft', 'open']:
            raise ValidationError(
                _("Solo se pueden auto-calcular puntajes en cuestionarios "
                  "en estado 'Draft' o 'In-Progress'.")
            )
        
        # Validar que existan preguntas
        lines_without_display = [
            line for line in self.line_ids if not line.display_type
        ]
        if not lines_without_display:
            raise ValidationError(
                _("El cuestionario no tiene preguntas válidas para calcular puntajes.")
            )
        
        # PASO 1: Distribuir puntajes entre preguntas sin puntaje
        questions_without_mark = [
            line for line in lines_without_display if not line.mark or line.mark == 0
        ]
        
        if questions_without_mark:
            # Calcular puntaje por pregunta
            score_per_question = 100.0 / len(lines_without_display)
            
            # Asignar puntaje a cada pregunta sin mark
            for line in questions_without_mark:
                line.write({'mark': score_per_question})
            
            self._log_auto_score_action(
                f"Distribución de puntajes inicial: {score_per_question:.2f} puntos "
                f"por pregunta ({len(questions_without_mark)} preguntas sin puntaje)"
            )
        else:
            raise ValidationError(
                _("El cuestionario ya tiene puntajes asignados en todas sus preguntas. "
                  "No se realizó ningún cambio.")
            )
        
        # PASO 2: Procesar resultados existentes (intentos de estudiantes)
        results = self.env['op.quiz.result'].search([
            ('quiz_id', '=', self.id)
        ])
        
        results_updated_count = 0
        for result in results:
            self._process_quiz_result(result)
            results_updated_count += 1
        
        # PASO 3: Sincronizar con gradebook si está disponible
        if self._is_grading_module_installed():
            self._sync_with_gradebook()
        
        # Mensaje de confirmación
        message = _(
            "✓ Auto-scoring completado exitosamente.\n"
            f"- {len(questions_without_mark)} preguntas fueron configuradas con "
            f"{100.0/len(lines_without_display):.2f} puntos cada una\n"
            f"- {results_updated_count} intentos de estudiantes fueron re-evaluados\n"
            f"- Puntaje total del cuestionario: {self.total_marks:.2f} puntos"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-scoring de Cuestionario'),
                'message': message,
                'type': 'success',
                'sticky': True,
            }
        }
    
    def _process_quiz_result(self, result):
        """
        Procesa un resultado/intento específico:
        - Recalcula puntajes de respuestas basado en correct/incorrect
        - Actualiza el total de puntaje del resultado
        """
        if not result.line_ids:
            return
        
        total_score = 0.0
        
        for result_line in result.line_ids:
            # Obtener la pregunta original del cuestionario
            question_line = result_line.line_id
            
            if not question_line:
                continue
            
            # Determinar si la respuesta es correcta
            is_correct = (
                result_line.given_answer and 
                result_line.given_answer.strip() == 
                (result_line.answer or '').strip()
            )
            
            # Asignar puntaje
            if is_correct:
                score = question_line.mark or 0.0
            else:
                score = 0.0
            
            # Actualizar la línea del resultado
            result_line.write({
                'score': score,
                'is_correct': is_correct,
            })
            
            total_score += score
        
        # Recalcular total y porcentaje del resultado
        total_marks = self.total_marks or 1.0
        percentage = (total_score / total_marks * 100.0) if total_marks > 0 else 0.0
        
        result.write({
            'obtain_mark': total_score,
            'percentage': percentage,
        })
    
    def _sync_with_gradebook(self):
        """
        Sincroniza los puntajes actualizados con el módulo de calificaciones
        (openeducat_grading) si está instalado.
        """
        try:
            # Buscar integraciones de gradebook
            GradebookLine = self.env.get('op.gradebook.line')
            if not GradebookLine:
                return
            
            results = self.env['op.quiz.result'].search([
                ('quiz_id', '=', self.id)
            ])
            
            for result in results:
                # Obtener estudiante del resultado
                student_id = result.student_id
                if not student_id:
                    continue
                
                # Buscar líneas de gradebook correspondientes
                gradebook_lines = GradebookLine.search([
                    ('student_id', '=', student_id.id),
                    ('value', 'ilike', self.name),
                ])
                
                for gb_line in gradebook_lines:
                    gb_line.write({
                        'marks': result.obtain_mark,
                        'percentage': result.percentage,
                    })
                    
        except Exception as e:
            # Log del error pero no fallar el proceso
            self._log_auto_score_action(
                f"Advertencia en sincronización de gradebook: {str(e)}"
            )
    
    def _is_grading_module_installed(self):
        """
        Verifica si el módulo openeducat_grading está instalado y activado.
        """
        try:
            return bool(
                self.env['ir.module.module'].search([
                    ('name', '=', 'openeducat_grading'),
                    ('state', '=', 'installed')
                ])
            )
        except Exception:
            return False
    
    def _log_auto_score_action(self, notes):
        """
        Registra la acción de auto-scoring en el log interno del cuestionario.
        """
        user_id = self.env.user.id
        log_message = f"[Auto-Scoring] {notes} | Usuario: {self.env.user.name}"
        
        # Registrar en el chatter del quiz para auditoría
        self.message_post(body=log_message)
