from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class IrgAutoTranslate(models.Model):
    _name = "irg.auto.translate"
    _description = "IRG Auto Translate helper"

    name = fields.Char('Name')

    @api.model
    def cron_run(self):
        """Cron entry point: run a single paginated pass over op.subject.

        For now this is a safe skeleton: it iterates subjects in small batches
        and calls the record-level `_translate_record_fields` hook which is a
        no-op placeholder. This prevents crashes while the provider client is
        still implemented.
        """
        batch_size = 100
        offset = 0
        while True:
            subjects = self.env['op.subject'].search([], offset=offset, limit=batch_size)
            if not subjects:
                break
            _logger.info("IRG auto-translate cron processing %s subjects (offset=%s)", len(subjects), offset)
            try:
                subjects._translate_record_fields(lang='es')
            except Exception as e:
                _logger.exception("Error during auto-translate cron: %s", e)
            offset += batch_size
        return True
