from odoo import _, fields, models


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    x_last_regraded_on = fields.Datetime(string='Ultima recalificacion', readonly=True)
    x_last_regraded_by = fields.Many2one('res.users', string='Recalificado por', readonly=True)

    def action_regrade_attempt(self):
        for record in self:
            record._regrade_single_attempt()
        return True

    def _regrade_single_attempt(self):
        self.ensure_one()

        # Recalcula score del intento usando la logica de Survey y extensiones activas.
        if hasattr(self, '_compute_scoring_values'):
            self._compute_scoring_values()

        if hasattr(self, 'compute_answer_score_total'):
            self.compute_answer_score_total()

        write_vals = {
            'x_last_regraded_on': fields.Datetime.now(),
            'x_last_regraded_by': self.env.user.id,
        }

        if 'scoring_total' in self._fields:
            write_vals['scoring_total'] = self.scoring_total or 0.0
        if 'scoring_percentage' in self._fields:
            write_vals['scoring_percentage'] = self.scoring_percentage or 0.0

        # Dispara write para mantener efectos colaterales existentes (isep_survey/isep_gradebook).
        self.with_context(irg_regrade=True).write(write_vals)

        if not getattr(self, 'result_id', False):
            return

        # Mantiene la regla de mejor intento en libreta (misma logica funcional que send_result).
        score_for_gradebook = self._get_gradebook_score_from_attempt()
        if getattr(self, 'slide_partner_id', False) and 'answer_score_total' in self._fields:
            for attempt in self.slide_partner_id.user_input_ids:
                score_for_gradebook = max(score_for_gradebook, attempt.answer_score_total or 0.0)

        self.result_id.write({'scoring_total': score_for_gradebook})

    def _get_gradebook_score_from_attempt(self):
        self.ensure_one()
        if 'answer_score_total' in self._fields:
            return self.answer_score_total or 0.0
        return round((self.scoring_percentage or 0.0) / 10.0, 2)

    def action_regrade_attempts_bulk(self):
        for record in self:
            record._regrade_single_attempt()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recalificacion completada'),
                'message': _('Se recalificaron %s intentos.') % len(self),
                'type': 'success',
                'sticky': False,
            },
        }
