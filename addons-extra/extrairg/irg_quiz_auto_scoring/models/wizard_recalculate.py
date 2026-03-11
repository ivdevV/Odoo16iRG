# -*- coding: utf-8 -*-
###############################################################################
#
#    iRG Inc
#    Copyright (C) 2009-TODAY iRG Inc
#
###############################################################################

from odoo import _, api, fields, models


class SurveyAutoScoreWizard(models.TransientModel):
    _name = 'survey.auto_score.wizard'
    _description = 'Wizard para recalcular calificaciones de survey'

    survey_id = fields.Many2one(
        'survey.survey',
        string='Survey',
        readonly=True,
    )
    message = fields.Text(
        string='Mensaje',
        readonly=True,
        default='Los puntajes ya están asignados en todas las respuestas correctas. '
                '¿Desea recalcular las calificaciones de todos los intentos existentes?'
    )

    def action_recalculate(self):
        """Recalcular intentos sin redistribuir puntajes"""
        survey = self.survey_id
        
        # Buscar y recalcular todos los intentos
        user_inputs = self.env['survey.user_input'].search([
            ('survey_id', '=', survey.id)
        ])
        
        recalculated_count = 0
        for user_input in user_inputs:
            # Para cada línea de respuesta en el intento
            for line in user_input.user_input_line_ids:
                # Obtener respuesta seleccionada usando método que maneja múltiples campos
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
                    # Obtener el nuevo puntaje de esa opción
                    new_score = ans.answer_score or 0.0
                    # Actualizar el puntaje de la línea
                    line.answer_score = new_score
                    line.flush()
            
            # Recalcular el total de puntos del intento
            total_score = sum(user_input.user_input_line_ids.mapped('answer_score'))
            user_input.answer_score_total = total_score
            user_input.flush()
            recalculated_count += 1
        
        # Registrar la acción
        survey._log_auto_score_action(
            f"Recálculo de {recalculated_count} intentos existentes sin redistribuir puntajes."
        )
        
        # Mensaje de confirmación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recálculo completado'),
                'message': _(
                    f"✓ Se recalcularon exitosamente {recalculated_count} intentos.\n"
                    "Las calificaciones han sido actualizadas con los nuevos puntajes."
                ),
                'type': 'success',
                'sticky': True,
            }
        }

    def action_cancel(self):
        """Cancelar la operación"""
        return {'type': 'ir.actions.act_window_close'}
