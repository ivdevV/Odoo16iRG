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
        
        1. Valida que haya preguntas
        2. Distribuye 100 puntos equitativamente entre las preguntas
        3. Asigna esos puntajes a las opciones de respuesta correctas
        4. Recalcula los puntajes de todos los intentos existentes
        5. Registra la acción en auditoría (chatter)
        """
        self.ensure_one()
        
        # Validar que existan preguntas
        questions = self.question_ids.filtered(
            lambda q: q.question_type not in ['section_heading']
        )
        
        if not questions:
            raise ValidationError(
                _("El survey no tiene preguntas válidas para calcular puntajes.")
            )
        
        # Obtener todas las preguntas con respuestas correctas (sin restricción de puntaje previo)
        questions_with_correct = []
        for question in questions:
            correct_answers = question.suggested_answer_ids.filtered(
                lambda a: (
                    getattr(a, 'is_correct', False)
                    or getattr(a, 'answer_is_correct', False)
                    or getattr(a, 'correct', False)
                )
            )
            if correct_answers:
                questions_with_correct.append(question)
        
        if not questions_with_correct:
            raise ValidationError(
                _("El survey no tiene respuestas correctas definidas.")
            )
        
        # Calcular puntaje por pregunta
        score_per_question = 100.0 / len(questions_with_correct)
        
        # Asignar puntaje a las respuestas correctas de cada pregunta
        for question in questions_with_correct:
            # Obtener todas las opciones de respuesta correctas
            correct_answers = question.suggested_answer_ids.filtered(
                lambda a: (
                    getattr(a, 'is_correct', False)
                    or getattr(a, 'answer_is_correct', False)
                    or getattr(a, 'correct', False)
                )
            )
            # Asignar puntaje a respuestas correctas (se permite actualizar si ya existe puntaje)
            correct_answers.write({'answer_score': score_per_question})
        
        # Recalcular intentos existentes
        user_inputs = self.env['survey.user_input'].search([
            ('survey_id', '=', self.id)
        ])
        
        for user_input in user_inputs:
            # Recalcular cada línea de respuesta basándose en la opción seleccionada.
            # Soportar distintos nombres de campo para la referencia a la respuesta seleccionada
            for line in user_input.user_input_line_ids:
                ans = None
                if hasattr(line, 'answer_id') and getattr(line, 'answer_id'):
                    ans = line.answer_id
                elif hasattr(line, 'suggested_answer_id') and getattr(line, 'suggested_answer_id'):
                    ans = line.suggested_answer_id
                elif hasattr(line, 'value_answer_id') and getattr(line, 'value_answer_id'):
                    ans = line.value_answer_id
                elif hasattr(line, 'value_answer_ids') and getattr(line, 'value_answer_ids'):
                    # take first selected answer if multiple
                    ans = line.value_answer_ids and line.value_answer_ids[0] or None

                # Fallback: intentar emparejar por texto de respuesta cuando no exista vínculo directo
                if not ans:
                    val_text = getattr(line, 'value_text', False) or getattr(line, 'value', False) or None
                    if val_text:
                        for a in (getattr(line, 'question_id', False) and line.question_id.suggested_answer_ids or []):
                            try:
                                if (a.name or '').strip() == (val_text or '').strip():
                                    ans = a
                                    break
                            except Exception:
                                continue

                if ans:
                    new_score = getattr(ans, 'answer_score', 0.0) or 0.0
                    line.answer_score = new_score
                    line.flush()

            # Recalcular el total: preferir campo answer_score_total si existe, sino scoring_total
            total_score = sum(user_input.user_input_line_ids.mapped('answer_score'))
            if 'answer_score_total' in user_input._fields:
                try:
                    user_input.answer_score_total = total_score
                except Exception:
                    pass
            if 'scoring_total' in user_input._fields:
                try:
                    user_input.scoring_total = total_score
                except Exception:
                    pass
            # Ejecutar posibles recomputos adicionales de módulos extensores
            if hasattr(user_input, '_compute_scoring_values'):
                try:
                    user_input._compute_scoring_values()
                except Exception:
                    pass
            if hasattr(user_input, 'compute_answer_score_total'):
                try:
                    user_input.compute_answer_score_total()
                except Exception:
                    pass
            user_input.flush()
        
        # Registrar la acción
        self._log_auto_score_action(
            f"Distribución/actualización de puntajes: {score_per_question:.2f} puntos "
            f"por pregunta ({len(questions_with_correct)} preguntas con respuestas correctas). "
            f"Recalculados {len(user_inputs)} intentos existentes."
        )
        
        # Mensaje de confirmación
        message = _(
            "✓ Auto-scoring completado exitosamente.\n"
            f"- {len(questions_with_correct)} preguntas fueron configuradas\n"
            f"- {score_per_question:.2f} puntos por respuesta correcta\n"
            f"- {len(user_inputs)} intentos fueron recalculados"
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
    
    def _log_auto_score_action(self, notes):
        """
        Registra la acción de auto-scoring en el log interno del survey.
        """
        log_message = f"[Auto-Scoring] {notes} | Usuario: {self.env.user.name}"
        
        # Registrar en el chatter del survey para auditoría
        self.message_post(body=log_message)
