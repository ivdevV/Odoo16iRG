# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import ast
import logging

from odoo import SUPERUSER_ID, api
from odoo.osv import expression

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


def repair_analytic_domains(env):
    """Clear analytic_domain values that reference fields not on account.move.line.

    mis.report.instance and mis.report.instance.period both have an
    ``analytic_domain`` Text field whose value is evaluated and appended to the
    move-line query domain.  If a domain leaf references a field that does not
    exist on ``account.move.line`` (e.g. ``custom_value`` from
    ``product.attribute.custom.value``), the query will fail with
    ``ValueError: Invalid field account.move.line.<field>``.

    This function parses each stored domain, checks every leaf against the
    actual fields of ``account.move.line``, and resets invalid domains to
    ``[]``.
    """
    aml_fields = set(env["account.move.line"].sudo()._fields.keys())

    def _domain_has_invalid_field(domain_str):
        """Return True if any leaf field in domain_str is not in aml_fields."""
        try:
            domain = ast.literal_eval(domain_str or "[]")
            if not domain:
                return False
            # Walk every leaf; a leaf is a 3-tuple (field_path, op, value).
            for leaf in domain:
                if not expression.is_leaf(leaf):
                    continue
                field_path = leaf[0].split(".")[0]  # only check first segment
                if field_path not in aml_fields:
                    return True
        except Exception:
            # Unparseable domain — treat as invalid to be safe.
            return True
        return False

    fixed = 0
    for model_name in ("mis.report.instance", "mis.report.instance.period"):
        records = env[model_name].sudo().search([])
        for rec in records:
            domain_str = rec.analytic_domain
            if domain_str and domain_str.strip() not in ("[]", ""):
                if _domain_has_invalid_field(domain_str):
                    _logger.warning(
                        "irg_mis_builder_fix: clearing invalid analytic_domain "
                        "on %s id=%s: %s",
                        model_name,
                        rec.id,
                        domain_str,
                    )
                    rec.analytic_domain = "[]"
                    fixed += 1

    if fixed:
        _logger.info(
            "irg_mis_builder_fix: cleared %d invalid analytic_domain value(s).",
            fixed,
        )
    else:
        _logger.info(
            "irg_mis_builder_fix: all analytic_domain values are valid."
        )


def post_init_hook(cr, registry):
    """Run on first install."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    repair_move_lines_source(env)
    repair_analytic_domains(env)
