# -*- coding: utf-8 -*-
###############################################################################
#
#    iRG Inc
#    Copyright (C) 2009-TODAY iRG Inc
#
###############################################################################

from odoo import _, fields, models


class OpQuizResult(models.Model):
    _inherit = "op.quiz.result"
    
    # Campo para almacenar si una respuesta es correcta (para auditoría)
    obtain_mark = fields.Float(
        string="Puntaje Obtenido",
        help="Puntaje total obtenido en este intento del cuestionario"
    )
    
    # Este campo puede que ya exista, pero lo agregamos aquí para referencia
    # En caso de que no exista, se crearará en la BD
    
    def recalculate_score(self):
        """
        Método para recalcular puntajes de forma individual en un resultado.
        """
        if not self.line_ids:
            return
        
        quiz = self.quiz_id
        total_score = 0.0
        
        for result_line in self.line_ids:
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
            
            result_line.write({'score': score})
            total_score += score
        
        # Actualizar total
        total_marks = quiz.total_marks or 1.0
        percentage = (total_score / total_marks * 100.0) if total_marks > 0 else 0.0
        
        self.write({
            'obtain_mark': total_score,
            'percentage': percentage,
        })
