from odoo import models, fields


class IrgAutoTranslateSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    irg_auto_translate_provider = fields.Selection(
        [('none', 'None'), ('deepl', 'DeepL'), ('google', 'Google Translate')],
        string='Translation Provider', default='none', config_parameter='irg_auto_translate.provider'
    )

    irg_auto_translate_api_key = fields.Char(
        string='Translation API Key', config_parameter='irg_auto_translate.api_key'
    )
