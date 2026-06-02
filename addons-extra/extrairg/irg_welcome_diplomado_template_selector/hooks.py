# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['auto.admission.required'].action_irg_ensure_diplomado_welcome_template()
