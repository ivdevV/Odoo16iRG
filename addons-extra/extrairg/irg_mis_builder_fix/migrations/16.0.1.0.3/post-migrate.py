# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api

from odoo.addons.irg_mis_builder_fix.hooks import (
    repair_analytic_domains,
    repair_move_lines_source,
)


def migrate(cr, version):
    """Re-run all MIS report data repairs on module update.

    Also fixes spurious [("id", "=", X)] analytic_domain values left by the
    PostgreSQL ID-reuse corruption that caused empty Balance reports.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    repair_move_lines_source(env)
    repair_analytic_domains(env)
