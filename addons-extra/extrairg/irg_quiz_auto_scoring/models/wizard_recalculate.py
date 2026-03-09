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
        
        for user_input in user_inputs:
            # Recalcular el total de puntos del intento
            total_score = sum(user_input.user_input_line_ids.mapped('answer_score'))
            user_input.write({'answer_score_total': total_score})
        
        # Registrar la acción
        survey._log_auto_score_action(
            f"Recálculo de {len(user_inputs)} intentos existentes sin redistribuir puntajes."
        )
        
        # Mensaje de confirmación
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recálculo completado'),
                'message': _(
                    f"✓ Se recalcularon exitosamente {len(user_inputs)} intentos.\n"
                    "Las calificaciones han sido actualizadas."
                ),
                'type': 'success',
                'sticky': True,
            }
        }

    def action_cancel(self):
        """Cancelar la operación"""
        return {'type': 'ir.actions.act_window_close'}
