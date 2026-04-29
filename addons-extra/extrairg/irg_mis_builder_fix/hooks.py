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
    """Clear analytic_domain values that are invalid as account.move.line filters.

    Two classes of invalid domain are detected and cleared to ``[]``:

    1. **Invalid field** — a leaf references a field that does not exist on
       ``account.move.line`` (e.g. ``custom_value`` from
       ``product.attribute.custom.value``).  This caused
       ``ValueError: Invalid field account.move.line.<field>``.

    2. **Spurious ``id`` filter** — a domain of the form ``[("id", "=", X)]``
       where X is a small integer.  This residue is left by the PostgreSQL ID-
       reuse bug: the old ir.model ID (e.g. 1) was recycled and stored as the
       analytic_domain of the MIS instance, resulting in move-line queries that
       return 0 or 1 result instead of all journal entries.
    """
    aml_fields = set(env["account.move.line"].sudo()._fields.keys())

    def _domain_is_invalid(domain_str):
        """Return (is_invalid, reason) for a stored analytic_domain string."""
        try:
            domain = ast.literal_eval(domain_str or "[]")
            if not domain:
                return False, None
            for leaf in domain:
                if not expression.is_leaf(leaf):
                    continue
                field_path, operator, value = leaf[0], leaf[1], leaf[2]
                first_field = field_path.split(".")[0]

                # Case 1: field doesn't exist on account.move.line
                if first_field not in aml_fields:
                    return True, "unknown field '%s'" % first_field

                # Case 2: filtering by id = <small integer> is almost certainly
                # a residual from the ir.model ID-reuse corruption.
                # A legitimate analytic filter on account.move.line would never
                # restrict by a specific record id.
                if first_field == "id" and operator in ("=", "!=", "in", "not in"):
                    return True, "suspicious id filter: %s" % str(leaf)

        except Exception as exc:
            return True, "unparseable domain: %s" % exc
        return False, None

    fixed = 0
    for model_name in ("mis.report.instance", "mis.report.instance.period"):
        records = env[model_name].sudo().search([])
        for rec in records:
            domain_str = rec.analytic_domain
            if not domain_str or domain_str.strip() in ("[]", ""):
                continue
            invalid, reason = _domain_is_invalid(domain_str)
            if invalid:
                _logger.warning(
                    "irg_mis_builder_fix: clearing invalid analytic_domain "
                    "on %s id=%s (%s): %s",
                    model_name,
                    rec.id,
                    reason,
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
