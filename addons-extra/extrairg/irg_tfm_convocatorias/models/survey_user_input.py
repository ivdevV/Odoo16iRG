from odoo import api, models, _
from odoo.exceptions import UserError


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    @api.model_create_multi
    def create(self, vals_list):
        survey_ids = {
            vals.get('survey_id') or self.env.context.get('default_survey_id')
            for vals in vals_list
        } - {False, None}
        if self.env['survey.survey'].sudo().browse(list(survey_ids)).filtered(
            'irg_tfm_template_only'
        ):
            raise UserError(_(
                'Las plantillas TFM no admiten intentos nativos de Encuestas.'
            ))
        return super().create(vals_list)

    def write(self, vals):
        target = self.env['survey.survey']
        if vals.get('survey_id'):
            target = target.sudo().browse(vals['survey_id'])
        if self.filtered('survey_id.irg_tfm_template_only') or target.filtered(
            'irg_tfm_template_only'
        ):
            raise UserError(_(
                'Las plantillas TFM no admiten intentos nativos de Encuestas.'
            ))
        return super().write(vals)
