# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# Fields that must exist on a valid move-lines source model.
_REQUIRED_AML_FIELDS = {"debit", "credit", "account_id", "date", "company_id"}


def repair_move_lines_source(env):
    """Repair stale or mis-pointing move_lines_source on all mis.report records.

    Three cases are fixed:
    1. NULL — move_lines_source was never set.
    2. Dangling FK — the ir.model row was deleted (PostgreSQL ID reuse may
       point the column at a completely different model).
    3. Wrong model — move_lines_source points to a valid ir.model row but that
       model lacks the required AML fields (debit/credit/account_id/date/
       company_id).  This happens when Odoo recycles the old DB ID for a
       different model after a module update.
    """
    cr = env.cr

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

    # Case 1: NULL
    null_reports = env["mis.report"].sudo().search([("move_lines_source", "=", False)])

    # Case 2: Dangling FK (the ir.model row no longer exists).
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

    # Case 3: FK is valid but points to a model that lacks required AML fields.
    # This is the "ID reuse" scenario where PG assigned the old AML ir.model ID
    # to an entirely different model (e.g. product.attribute.custom.value).
    already_broken_ids = set(null_reports.ids) | set(dangling_ids)
    all_reports = env["mis.report"].sudo().search(
        [("move_lines_source", "!=", False), ("id", "not in", list(already_broken_ids))]
    )
    wrong_model_reports = env["mis.report"].sudo()
    for report in all_reports:
        source_field_names = set(report.move_lines_source.field_id.mapped("name"))
        if not _REQUIRED_AML_FIELDS.issubset(source_field_names):
            _logger.warning(
                "irg_mis_builder_fix: mis.report id=%s has move_lines_source "
                "pointing to model '%s' which lacks required AML fields. "
                "Will reset to account.move.line.",
                report.id,
                report.move_lines_source.model,
            )
            wrong_model_reports |= report

    to_fix = null_reports | dangling_reports | wrong_model_reports
    if to_fix:
        _logger.info(
            "irg_mis_builder_fix: repairing %d mis.report record(s) "
            "with invalid move_lines_source → setting to ir.model id=%s "
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


def post_init_hook(cr, registry):
    """Run on first install."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    repair_move_lines_source(env)
