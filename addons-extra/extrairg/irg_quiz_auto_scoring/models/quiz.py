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
        2. Si NO todas las preguntas tienen puntaje:
           - Divide 100 entre el número de preguntas
           - Asigna ese puntaje a cada pregunta
        3. Registra la acción en auditoría (chatter)
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
        
        # Distribuir puntajes entre preguntas sin puntaje
        questions_without_mark = questions.filtered(
            lambda q: not q.answer_score or q.answer_score == 0
        )
        
        if not questions_without_mark:
            raise ValidationError(
                _("El survey ya tiene puntajes asignados en todas sus preguntas. "
                  "No se realizó ningún cambio.")
            )
        
        # Calcular puntaje por pregunta
        score_per_question = 100.0 / len(questions)
        
        # Asignar puntaje a cada pregunta sin puntaje
        for question in questions_without_mark:
            question.write({'answer_score': score_per_question})
        
        # Registrar la acción
        self._log_auto_score_action(
            f"Distribución de puntajes: {score_per_question:.2f} puntos "
            f"por pregunta ({len(questions_without_mark)} preguntas sin puntaje; "
            f"{len(questions)} preguntas totales)"
        )
        
        # Mensaje de confirmación
        total_marks = sum(q.answer_score or 0 for q in questions)
        message = _(
            "✓ Auto-scoring completado exitosamente.\n"
            f"- {len(questions_without_mark)} preguntas fueron configuradas\n"
            f"- {score_per_question:.2f} puntos por pregunta\n"
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
    
    def _log_auto_score_action(self, notes):
        """
        Registra la acción de auto-scoring en el log interno del survey.
        """
        log_message = f"[Auto-Scoring] {notes} | Usuario: {self.env.user.name}"
        
        # Registrar en el chatter del survey para auditoría
        self.message_post(body=log_message)
