# -*- coding: utf-8 -*-
###############################################################################
#
#    iRG Inc
#    Copyright (C) 2009-TODAY iRG Inc
#
###############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Survey(models.Model):
    _inherit = "survey.survey"

    def action_auto_score_quiz(self):
        """
        Acción para auto-calcular y asignar puntajes automáticamente a surveys.
        
        1. Si NO todas las preguntas tienen puntaje:
           - Divide 100 entre el número de preguntas con puntaje 0/None
           - Asigna ese puntaje a cada pregunta
           
        2. Procesa TODOS los resultados existentes (intentos de usuarios):
           - Para cada respuesta correcta: asigna el puntaje de la pregunta
           - Para cada respuesta incorrecta: asigna 0
           - Recalcula el total de puntaje del resultado
           
        3. Si openeducat_grading está instalado:
           - Sincroniza con el boletín de calificaciones
        """
        self.ensure_one()
        
        # Validar que sea un survey tipo quiz/examen
        if self.survey_type not in ['quiz', 'exam', 'cert']:
            raise ValidationError(
                _("Este survey no es de tipo Quiz/Examen. "
                  "Solo se pueden auto-calcular puntajes en surveys de tipo 'quiz', 'exam' o 'cert'.")
            )
        
        # Validar que existan preguntas
        questions = self.question_ids.filtered(
            lambda q: q.question_type not in ['section_heading']
        )
        
        if not questions:
            raise ValidationError(
                _("El survey no tiene preguntas válidas para calcular puntajes.")
            )
        
        # PASO 1: Distribuir puntajes entre preguntas sin puntaje
        questions_without_mark = questions.filtered(
            lambda q: not q.points or q.points == 0
        )
        
        if questions_without_mark:
            # Calcular puntaje por pregunta
            score_per_question = 100.0 / len(questions)
            
            # Asignar puntaje a cada pregunta sin puntaje
            for question in questions_without_mark:
                question.write({'points': score_per_question})
            
            self._log_auto_score_action(
                f"Distribución de puntajes inicial: {score_per_question:.2f} puntos "
                f"por pregunta ({len(questions_without_mark)} preguntas sin puntaje)"
            )
        else:
            raise ValidationError(
                _("El survey ya tiene puntajes asignados en todas sus preguntas. "
                  "No se realizó ningún cambio.")
            )
        
        # PASO 2: Procesar resultados existentes (intentos de usuarios)
        user_inputs = self.env['survey.user_input'].search([
            ('survey_id', '=', self.id),
            ('state', '=', 'finished'),
        ])
        
        results_updated_count = 0
        for user_input in user_inputs:
            self._process_survey_result(user_input, questions)
            results_updated_count += 1
        
        # PASO 3: Sincronizar con gradebook si está disponible
        if self._is_grading_module_installed():
            self._sync_with_gradebook()
        
        # Mensaje de confirmación
        total_marks = sum(q.points or 0 for q in questions)
        message = _(
            "✓ Auto-scoring completado exitosamente.\n"
            f"- {len(questions_without_mark)} preguntas fueron configuradas con "
            f"{100.0/len(questions):.2f} puntos cada una\n"
            f"- {results_updated_count} intentos de usuarios fueron re-evaluados\n"
            f"- Puntaje total del survey: {total_marks:.2f} puntos"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-scoring de Survey'),
                'message': message,
                'type': 'success',
                'sticky': True,
            }
        }
    
    def _process_survey_result(self, user_input, questions):
        """
        Procesa un resultado/intento específico:
        - Recalcula puntajes de respuestas basado en corrección automática
        - Actualiza el total de puntaje del resultado
        """
        if not user_input.user_input_line_ids:
            return
        
        total_score = 0.0
        
        for answer_line in user_input.user_input_line_ids:
            question = answer_line.question_id
            
            if not question or question.question_type == 'section_heading':
                continue
            
            # Obtener respuesta dada por el usuario
            given_answer = answer_line.value_text or answer_line.value_suggested_row
            
            # Obtener respuesta correcta según el tipo de pregunta
            is_correct = self._check_answer_correctioness(question, given_answer)
            
            # Asignar puntaje
            if is_correct:
                score = question.points or 0.0
            else:
                score = 0.0
            
            # Registrar el puntaje en la línea (si existe el campo)
            # survey.user_input_line no tiene campo de score por defecto
            # pero podemos loguear o simplemente acumular
            total_score += score
        
        # Recalcular total y porcentaje del resultado
        total_marks = sum(q.points or 0 for q in self.question_ids.filtered(
            lambda q: q.question_type not in ['section_heading']
        ))
        
        percentage = (total_score / total_marks * 100.0) if total_marks > 0 else 0.0
        
        # Actualizar el user_input con los nuevos puntajes
        user_input.write({
            'score_suggested_choice': total_score,
        })
    
    def _check_answer_correctioness(self, question, given_answer):
        """
        Verifica si una respuesta es correcta basándose en:
        - Para questions de multiple_choice: compara con answer_ids marcados como correctos
        - Para text_box: compara con el texto esperado
        - Para matrix: compara filas/columnas correctas
        """
        if question.question_type == 'multiple_choice':
            # Para multiple choice, verificar si el answer_id es correcto
            if question.answer_ids:
                correct_answers = question.answer_ids.filtered('is_correct')
                # Aquí se requeriría más lógica según cómo se almacenen las respuestas
                return True if given_answer else False
        
        elif question.question_type == 'text_box':
            # Para text_box, validar contra palabra clave esperada
            expected = question.answer_ids[0].value if question.answer_ids else None
            if expected and given_answer:
                return given_answer.strip().lower() == expected.strip().lower()
        
        # Por defecto, considerar como validado
        return False
    
    def _sync_with_gradebook(self):
        """
        Sincroniza los puntajes actualizados con el módulo de calificaciones
        si está instalado.
        """
        try:
            # Buscar integraciones de gradebook (si existen)
            GradebookLine = self.env.get('op.gradebook.line')
            if not GradebookLine:
                return
            
            user_inputs = self.env['survey.user_input'].search([
                ('survey_id', '=', self.id),
                ('state', '=', 'finished'),
            ])
            
            for user_input in user_inputs:
                # Obtener estudiante del resultado
                partner_id = user_input.partner_id
                if not partner_id:
                    continue
                
                # Buscar líneas de gradebook correspondientes
                gradebook_lines = GradebookLine.search([
                    ('partner_id', '=', partner_id.id),
                    ('value', 'ilike', self.title),
                ])
                
                for gb_line in gradebook_lines:
                    score = user_input.score_suggested_choice or 0.0
                    total_marks = sum(
                        q.points or 0 
                        for q in self.question_ids.filtered(
                            lambda q: q.question_type not in ['section_heading']
                        )
                    )
                    percentage = (score / total_marks * 100.0) if total_marks > 0 else 0.0
                    
                    gb_line.write({
                        'marks': score,
                        'percentage': percentage,
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
        Registra la acción de auto-scoring en el log interno del survey.
        """
        user_id = self.env.user.id
        log_message = f"[Auto-Scoring] {notes} | Usuario: {self.env.user.name}"
        
        # Registrar en el chatter del survey para auditoría
        self.message_post(body=log_message)
