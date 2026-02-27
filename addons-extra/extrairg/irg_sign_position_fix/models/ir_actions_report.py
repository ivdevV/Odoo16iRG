from odoo import models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def get_raimon_signature_positions(self):
        """Return a mapping page=index -> normalized posY for the raimon
        signature image on the prematricula report.

        The values are expressed as fractions of the page height (0.0 bottom,
        1.0 top) and should exactly match the Y coordinate where the report
        template draws the ``firma_raimon.png`` asset.  Keeping the constants
        here ensures the sign fields created in ``sale.order`` always align with
        the visible signature in the PDF; if the report layout changes,
        update these numbers accordingly.

        A more advanced implementation could inspect the generated PDF and
        compute the coordinates dynamically (e.g. using PyPDF2), but a simple
        shared-constant approach is sufficient and avoids extra dependencies.
        """
        # By default we know raimon signature appears on page 1 and 3
        # at these normalized vertical positions; tweak if report layout moves.
        return {
            1: 0.710,
            3: 0.650,
        }
