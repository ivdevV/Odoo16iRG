# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api

from odoo.addons.irg_mis_builder_fix.hooks import repair_move_lines_source


def migrate(cr, version):
    """Re-run the move_lines_source repair on every module update.

    This is needed because post_init_hook only fires on first install.
    The repair detects three failure modes:
      - NULL move_lines_source
      - Dangling FK (ir.model row was deleted)
      - Wrong model FK (PostgreSQL reused the old ID for a different model)
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    repair_move_lines_source(env)
