from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class OpCourse(models.Model):
    _inherit = 'op.course'

    # Re-declare name as translatable
    name = fields.Char(translate=True)
    description = fields.Html(translate=True)

    @api.model
    def create(self, vals):
        record = super(OpCourse, self).create(vals)
        # Optionally trigger translation for newly created course
        try:
            if not self.env.context.get('irg_auto_translate_internal'):
                self._auto_translate_record(record)
        except Exception:
            _logger.exception('Auto-translate on create failed')
        return record

    def write(self, vals):
        res = super(OpCourse, self).write(vals)
        if not self.env.context.get('irg_auto_translate_internal'):
            try:
                for rec in self:
                    self._auto_translate_record(rec)
            except Exception:
                _logger.exception('Auto-translate on write failed')
        return res

    def _auto_translate_record(self, record):
        # Synchronous simple translation for name and description.
        service = self.env['irg.translation.service']
        params = self.env['ir.config_parameter'].sudo()
        default_source = params.get_param('irg.translate.default_source') or 'es'
        provider = params.get_param('irg.translate.provider') or 'deepl'

        # get active website languages
        langs = self.env['res.lang'].sudo().search([('active', '=', True)])
        source_text_name = record.name or ''
        source_text_desc = record.description or ''
        for lang in langs:
            code = lang.code
            if not code or code == default_source:
                continue
            try:
                translated = service.translate(source_text_name, default_source, code)
                if translated:
                    record.with_context(irg_auto_translate_internal=True, lang=code).write({'name': translated})
                if source_text_desc:
                    translated_desc = service.translate(source_text_desc, default_source, code)
                    if translated_desc:
                        record.with_context(irg_auto_translate_internal=True, lang=code).write({'description': translated_desc})
            except Exception:
                _logger.exception('Error translating course %s to %s', record.id, code)
