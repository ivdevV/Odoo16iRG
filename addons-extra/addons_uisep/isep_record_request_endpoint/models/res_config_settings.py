from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    upload_url = fields.Char(string='Url de carga de archivos', config_parameter='upload_url')
    ocr_raw_url = fields.Char(string='Url de OCR RAW', config_parameter='ocr_raw_url')

