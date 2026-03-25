# -*- coding: utf-8 -*-
from . import models


def post_init_hook(cr, registry):
    """Initialize default config parameters safely (no XML to avoid UniqueViolation)."""
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env['ir.config_parameter']
    if not ICP.get_param('irg_timetable_csv_import.watch_dir', default=None):
        ICP.set_param('irg_timetable_csv_import.watch_dir', '')
