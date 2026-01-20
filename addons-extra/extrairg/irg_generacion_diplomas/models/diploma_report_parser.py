from odoo import models, api

class DiplomaReport(models.AbstractModel):
    _name = 'report.irg_generacion_diplomas.report_diploma_document'
    _description = 'Diploma Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'irg.diploma.wizard',
            'data': data.get('form'),
        }
