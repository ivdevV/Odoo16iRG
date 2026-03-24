import logging
import json
from odoo import models

_logger = logging.getLogger(__name__)

try:
    import requests
except Exception:
    requests = None


class IrgTranslationService(models.AbstractModel):
    _name = 'irg.translation.service'
    _description = 'IRG Translation Service (DeepL/Google)'

    def _deepl_translate(self, text, target_lang, auth_key):
        if not requests:
            _logger.error('requests library not available for DeepL calls')
            return None
        url = 'https://api.deepl.com/v2/translate'
        data = {
            'auth_key': auth_key,
            'text': text,
            'target_lang': target_lang.upper()
        }
        try:
            resp = requests.post(url, data=data, timeout=15)
            if resp.status_code == 200:
                j = resp.json()
                return j.get('translations', [{}])[0].get('text')
            _logger.error('DeepL returned status %s: %s', resp.status_code, resp.text)
        except Exception as e:
            _logger.exception('Error calling DeepL: %s', e)
        return None

    def translate(self, text, source_lang, target_lang):
        params = self.env['ir.config_parameter'].sudo()
        provider = params.get_param('irg.translate.provider') or 'deepl'
        api_key = params.get_param('irg.translate.api_key')
        if not api_key:
            _logger.warning('No API key set for irg.translate.api_key')
            return None
        if provider == 'deepl':
            return self._deepl_translate(text, target_lang, api_key)
        _logger.warning('Translation provider %s not implemented', provider)
        return None
