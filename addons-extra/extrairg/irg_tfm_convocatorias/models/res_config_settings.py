from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_irg_tfm_outline_survey(self):
        return self.env.ref(
            'irg_tfm_convocatorias.tfm_outline_survey',
            raise_if_not_found=False,
        )

    irg_tfm_outline_survey_id = fields.Many2one(
        'survey.survey',
        string='Encuesta de Esquema TFM',
        config_parameter='irg_tfm_convocatorias.outline_survey_id',
        default=_default_irg_tfm_outline_survey,
        domain=[('irg_tfm_template_only', '=', True)],
        help='Plantilla editable utilizada al crear nuevos borradores de Esquema.',
    )
