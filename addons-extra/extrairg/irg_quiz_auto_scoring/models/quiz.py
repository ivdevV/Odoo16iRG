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
        
        # Filtrar preguntas sin puntajes asignados en sus opciones de respuesta correctas
        questions_without_mark = []
        for question in questions:
            correct_answers = question.suggested_answer_ids.filtered(
                lambda a: a.is_correct and (not a.answer_score or a.answer_score == 0)
            )
            if correct_answers:
                questions_without_mark.append(question)
        
        if not questions_without_mark:
            # Abrir wizard para permitir recalcular intentos
            wizard = self.env['survey.auto_score.wizard'].create({
                'survey_id': self.id,
            })
            return {
                'name': _('Recalcular Calificaciones'),
                'type': 'ir.actions.act_window',
                'res_model': 'survey.auto_score.wizard',
                'res_id': wizard.id,
                'view_mode': 'form',
                'target': 'new',
            }
        
        # Calcular puntaje por pregunta
        score_per_question = 100.0 / len(questions)
        
        # Asignar puntaje a las respuestas correctas de cada pregunta sin puntaje
        for question in questions_without_mark:
            # Obtener todas las opciones de respuesta correctas
            correct_answers = question.suggested_answer_ids.filtered(
                lambda a: a.is_correct
            )
            # Asignar puntaje solo a respuestas correctas
            correct_answers.write({'answer_score': score_per_question})
        
        # Recalcular intentos existentes
        user_inputs = self.env['survey.user_input'].search([
            ('survey_id', '=', self.id)
        ])
        
        for user_input in user_inputs:
            # Recalcular cada línea de respuesta basándose en la opción seleccionada
            for line in user_input.user_input_line_ids:
                if line.answer_id:
                    # Obtener el nuevo puntaje asignado a esa opción
                    new_score = line.answer_id.answer_score or 0.0
                    # Actualizar directamente el campo answer_score
                    # Usar flush para asegurar que se persista inmediatamente
                    line.answer_score = new_score
                    line.flush()
            
            # Recalcular el total: suma de todos los answer_scores de las líneas
            total_score = sum(user_input.user_input_line_ids.mapped('answer_score'))
            user_input.answer_score_total = total_score
            user_input.flush()
        
        # Registrar la acción
        self._log_auto_score_action(
            f"Distribución de puntajes: {score_per_question:.2f} puntos "
            f"por pregunta ({len(questions_without_mark)} preguntas sin puntaje; "
            f"{len(questions)} preguntas totales). "
            f"Recalculados {len(user_inputs)} intentos existentes."
        )
        
        # Mensaje de confirmación
        message = _(
            "✓ Auto-scoring completado exitosamente.\n"
            f"- {len(questions_without_mark)} preguntas fueron configuradas\n"
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
