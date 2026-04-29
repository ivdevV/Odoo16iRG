# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# Default fallback for the account model when move_lines_source is stale/unset.
# account.move.line.account_id always points to account.account in standard Odoo.
_FALLBACK_ACCOUNT_MODEL = "account.account"


class MisReport(models.Model):
    _inherit = "mis.report"

    @api.depends("move_lines_source")
    def _compute_account_model(self):
        """Override to guard against a stale move_lines_source reference.

        After an Odoo module update the ir.model record for account.move.line
        can be deleted and recreated with a new ID.  When that happens,
        move_lines_source resolves to an empty recordset, _compute_account_model
        sets account_model to False, and AEP.__init__ crashes with
        KeyError: False when it does self.env[account_model].

        This override calls super() and then replaces any falsy result with the
        known-good fallback 'account.account'.
        """
        super()._compute_account_model()
        for record in self:
            if not record.account_model:
                _logger.warning(
                    "mis.report id=%s has an invalid or missing move_lines_source "
                    "(id=%s).  Falling back to account_model='%s'. "
                    "Run the irg_mis_builder_fix post_init_hook or manually set "
                    "move_lines_source to fix this permanently.",
                    record.id,
                    record.move_lines_source.id,
                    _FALLBACK_ACCOUNT_MODEL,
                )
                record.account_model = _FALLBACK_ACCOUNT_MODEL
