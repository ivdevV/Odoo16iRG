from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class OpSubjectTranslate(models.Model):
    _inherit = "op.subject"

    # Re-declare `name` as translatable. This instructs Odoo to store and
    # serve translations for subject names.
    name = fields.Char('Name', size=128, required=True, translate=True)

    def _translate_record_fields(self, lang):
        """Placeholder for calling an external translation provider.

        Currently this is a skeleton: it logs the intended action. Later
        this should call a provider client (DeepL/Google) configured by
        system parameters and write translated values into the i18n
        system (or set field translations directly).
        """
        for record in self:
            _logger.info("Requested translation for op.subject %s -> %s", record.id, lang)
        return True
