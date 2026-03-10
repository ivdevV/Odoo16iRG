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
                if line.answer_id:
                    # Obtener el nuevo puntaje de esa opción
                    new_score = line.answer_id.answer_score or 0.0
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
