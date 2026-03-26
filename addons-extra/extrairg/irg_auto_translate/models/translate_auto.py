# -*- coding: utf-8 -*-
"""
irg_auto_translate — translate_auto.py

Makes op.course.name and op.subject.name translatable, flags records when
their name changes, and provides the cron-callable method that calls
DeepL or Google Translate synchronously (no threads, no asyncio).

Thread-safety note:
    Odoo 16 uses gevent monkey-patching. Native threading.Thread usage
    causes KeyError crashes in the ImDispatch bus. This module avoids all
    threading and asyncio; urllib is gevent-patched and therefore safe.
"""
import json
import logging
import urllib.parse
import urllib.request

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# Maximum records to translate per cron run (keeps cron short)
BATCH_LIMIT = 20

# Map Odoo lang codes to DeepL target language codes
DEEPL_LANG_MAP = {
    'en': 'EN-US',
    'fr': 'FR',
    'it': 'IT',
    'pt': 'PT-PT',
    'ca': None,   # DeepL does not support Catalan — skip silently
    'de': 'DE',
    'nl': 'NL',
}

# Map Odoo lang codes to Google Translate target language codes
GOOGLE_LANG_MAP = {
    'en': 'en',
    'fr': 'fr',
    'it': 'it',
    'pt': 'pt',
    'ca': 'ca',
    'de': 'de',
    'nl': 'nl',
}


# ---------------------------------------------------------------------------
# Inherited models — add translate=True + pending-translation flag
# ---------------------------------------------------------------------------

class OpCourse(models.Model):
    _inherit = 'op.course'

    # Re-declare to add translate=True (name was non-translatable in
    # openeducat_core). After -u irg_auto_translate the DB column gains
    # an ir.translation row per language.
    name = fields.Char(translate=True)

    irg_needs_translation = fields.Boolean(
        string='Needs auto-translation',
        default=False,
        help='Set automatically when the course name changes. '
             'The nightly cron will translate it to all active languages.',
    )

    def write(self, vals):
        # When name is updated, queue this record for (re-)translation.
        # We set the flag inside vals so only one write call is made,
        # avoiding any risk of recursion.
        if 'name' in vals and 'irg_needs_translation' not in vals:
            vals['irg_needs_translation'] = True
        return super().write(vals)

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['irg_needs_translation'] = True
        return super().create(vals)

    # ------------------------------------------------------------------
    # Cron entry-point — called by ir.cron.  Must be @api.model so the
    # cron record can specify model=op.course method=_irg_translate_cron.
    # ------------------------------------------------------------------
    @api.model
    def _irg_translate_cron(self):
        """
        Synchronous batch translation entry-point for ir.cron.
        Translates pending op.course AND op.subject records to all active
        website languages that are NOT Spanish (the source language).

        NO threads, NO asyncio — all urllib calls are synchronous and
        gevent-compatible (gevent monkey-patches urllib at startup).
        """
        service = _IrgTranslationService(self.env)
        if not service.api_key:
            _logger.warning(
                'irg_auto_translate: no API key in ir.config_parameter '
                '(key: irg.translate.api_key). Skipping cron run.'
            )
            return

        target_langs = service.get_target_languages()
        if not target_langs:
            return

        processed = 0
        for model_name, field_name in (
            ('op.course', 'name'),
            ('op.subject', 'name'),
        ):
            if processed >= BATCH_LIMIT:
                break
            try:
                Model = self.env[model_name]
            except KeyError:
                _logger.warning(
                    'irg_auto_translate: model %s not found, skipping.',
                    model_name,
                )
                continue

            pending = Model.search(
                [('irg_needs_translation', '=', True)],
                limit=BATCH_LIMIT - processed,
            )
            for rec in pending:
                service.translate_record(rec, field_name, target_langs)
                # Clear flag — use super write so we don't re-flag ourselves
                models.Model.write(rec, {'irg_needs_translation': False})
                processed += 1

        _logger.info(
            'irg_auto_translate: cron run translated %d record(s).', processed
        )


class OpSubject(models.Model):
    _inherit = 'op.subject'

    name = fields.Char(translate=True)

    irg_needs_translation = fields.Boolean(
        string='Needs auto-translation',
        default=False,
    )

    def write(self, vals):
        if 'name' in vals and 'irg_needs_translation' not in vals:
            vals['irg_needs_translation'] = True
        return super().write(vals)

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['irg_needs_translation'] = True
        return super().create(vals)


# ---------------------------------------------------------------------------
# Internal translation service helper (NOT an Odoo model)
# ---------------------------------------------------------------------------

class _IrgTranslationService:
    """
    Pure Python helper — not an Odoo model, no ORM record.
    Encapsulates the synchronous HTTP calls to DeepL / Google Translate.

    Thread-safety: uses only urllib (gevent-patched), no threading.Thread.
    Timeout: 5 s per HTTP request to avoid blocking cron workers.
    """

    def __init__(self, env):
        cfg = env['ir.config_parameter'].sudo()
        self.provider = cfg.get_param('irg.translate.provider', default='deepl')
        self.api_key = cfg.get_param('irg.translate.api_key', default='')
        self.env = env

    def get_target_languages(self):
        """Return all active res.lang records whose code is NOT Spanish."""
        all_langs = self.env['res.lang'].search([('active', '=', True)])
        return [l for l in all_langs if not (l.code or '').startswith('es')]

    def translate_record(self, record, field_name, target_langs):
        """Translate one record's field into all target languages."""
        # Source text is always the Spanish (es) value
        source_text = getattr(record, field_name, None)
        if not source_text:
            return
        for lang in target_langs:
            iso2 = (lang.code or '')[:2].lower()
            translated = self._call_api(source_text, 'es', iso2)
            if translated and translated.strip() != source_text.strip():
                record.with_context(lang=lang.code).write(
                    {field_name: translated}
                )

    def _call_api(self, text, source_iso2, target_iso2):
        """Dispatch to the configured provider. Returns translated str or None."""
        if self.provider == 'google':
            return self._call_google(text, source_iso2, target_iso2)
        # Default: DeepL free API
        return self._call_deepl(text, source_iso2, target_iso2)

    def _call_deepl(self, text, source_iso2, target_iso2):
        """
        Call DeepL free API (api-free.deepl.com).
        Uses urllib — synchronous, gevent-compatible, 5 s timeout.
        """
        target_code = DEEPL_LANG_MAP.get(target_iso2)
        if not target_code:
            # Language not supported by DeepL (e.g. Catalan) — skip silently
            return None

        url = 'https://api-free.deepl.com/v2/translate'
        payload = urllib.parse.urlencode({
            'auth_key': self.api_key,
            'text': text,
            'source_lang': source_iso2.upper(),
            'target_lang': target_code,
        }).encode('utf-8')

        try:
            req = urllib.request.Request(
                url, data=payload, method='POST',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data['translations'][0]['text']
        except Exception as exc:
            _logger.warning('irg_auto_translate DeepL error (%s→%s): %s',
                            source_iso2, target_iso2, exc)
            return None

    def _call_google(self, text, source_iso2, target_iso2):
        """
        Call Google Cloud Translation API v2 (Basic).
        Uses urllib — synchronous, gevent-compatible, 5 s timeout.
        """
        target_code = GOOGLE_LANG_MAP.get(target_iso2, target_iso2)

        url = 'https://translation.googleapis.com/language/translate/v2'
        payload = urllib.parse.urlencode({
            'q': text,
            'source': source_iso2,
            'target': target_code,
            'key': self.api_key,
            'format': 'text',
        }).encode('utf-8')

        try:
            req = urllib.request.Request(
                url, data=payload, method='POST',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data['data']['translations'][0]['translatedText']
        except Exception as exc:
            _logger.warning('irg_auto_translate Google error (%s→%s): %s',
                            source_iso2, target_iso2, exc)
            return None
