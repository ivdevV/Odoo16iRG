# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api

from . import models


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.partner'].with_context(
        irg_dotado_silent=True
    )._cron_recompute_moroso()
