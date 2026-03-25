# -*- coding: utf-8 -*-
# irg_auto_translate
# IMPORTANT: This module deliberately uses NO threading.Thread, NO asyncio,
# NO daemon processes. All external API calls happen synchronously inside
# ir.cron, which is Odoo/gevent-safe. This avoids the KeyError/_limbo issue
# observed when native threads are mixed with gevent greenlets.
import logging

from . import models


_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    After installation, queue ALL existing op.course and op.subject records
    for translation so they are picked up by the nightly cron.
    Wrapped in try/except per model so an absent openeducat module doesn't
    break the install.
    """
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    config = env['ir.config_parameter'].sudo()
    if not config.get_param('irg.translate.provider'):
        config.set_param('irg.translate.provider', 'deepl')
    if config.get_param('irg.translate.api_key', default=None) is None:
        config.set_param('irg.translate.api_key', '')

    for model_name in ('op.course', 'op.subject'):
        try:
            if model_name in env:
                env[model_name].search([]).write({'irg_needs_translation': True})
        except Exception as exc:
            _logger.warning(
                'irg_auto_translate post_init_hook: could not queue %s: %s',
                model_name, exc,
            )
