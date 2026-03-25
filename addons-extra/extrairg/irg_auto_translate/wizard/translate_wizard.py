from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class IrgTranslateWizard(models.TransientModel):
    _name = 'irg.translate.wizard'
    _description = 'IRG Translate Wizard'

    model_name = fields.Selection([('op.subject', 'Subject')], string='Model', required=True, default='op.subject')
    lang_to = fields.Char('Target language (code)', required=True, default='es')
    batch_size = fields.Integer('Batch size', default=50)
    offset = fields.Integer('Offset', default=0)

    def action_run(self):
        """Run a single batch of translations for the selected model.

        This is intentionally conservative: it calls the model hook
        `_translate_record_fields` for each batch. Real provider calls
        should be implemented in that hook or in a dedicated provider
        client module.
        """
        Model = self.env[self.model_name]
        records = Model.search([], offset=self.offset, limit=self.batch_size)
        _logger.info("IRG translate wizard: running batch offset=%s size=%s", self.offset, len(records))
        if records:
            records._translate_record_fields(self.lang_to)
        return {'type': 'ir.actions.act_window_close'}
