from odoo import models


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    def action_open_txt_import_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Importar preguntas TXT',
            'res_model': 'irg.survey.txt.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_survey_id': self.id,
            },
        }
