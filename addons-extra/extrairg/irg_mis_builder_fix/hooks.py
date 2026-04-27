# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Repair stale move_lines_source references on all mis.report records.

    After an Odoo module update the ir.model record for account.move.line may
    have been deleted and recreated with a new database ID.  Any mis.report row
    whose move_lines_source FK still points to the old (orphaned) ID will have
    move_lines_source resolved as False, which causes KeyError: False when
    printing MIS reports.

    This hook:
    1. Finds the current ir.model record for 'account.move.line'.
    2. Writes that ID onto every mis.report whose move_lines_source is either
       NULL (never set) or no longer resolves to a live ir.model row.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    aml_model = (
        env["ir.model"]
        .sudo()
        .search([("model", "=", "account.move.line")], limit=1)
    )
    if not aml_model:
        _logger.error(
            "irg_mis_builder_fix: ir.model record for 'account.move.line' not found. "
            "Cannot repair mis.report records automatically."
        )
        return

    # Find reports whose move_lines_source is NULL (False in ORM terms).
    null_reports = env["mis.report"].sudo().search([("move_lines_source", "=", False)])

    # Also find reports whose move_lines_source FK points to an ir.model record
    # that no longer exists (dangling FK — the ORM hides it as False too, but a
    # direct SQL check is more reliable here).
    cr.execute(
        """
        SELECT r.id
        FROM mis_report r
        LEFT JOIN ir_model m ON m.id = r.move_lines_source
        WHERE r.move_lines_source IS NOT NULL
          AND m.id IS NULL
        """
    )
    dangling_ids = [row[0] for row in cr.fetchall()]
    dangling_reports = env["mis.report"].sudo().browse(dangling_ids)

    to_fix = null_reports | dangling_reports
    if to_fix:
        _logger.info(
            "irg_mis_builder_fix: repairing %d mis.report record(s) "
            "with missing/stale move_lines_source → setting to ir.model id=%s "
            "(account.move.line).",
            len(to_fix),
            aml_model.id,
        )
        to_fix.write({"move_lines_source": aml_model.id})
    else:
        _logger.info(
            "irg_mis_builder_fix: all mis.report records have a valid "
            "move_lines_source. No repair needed."
        )
