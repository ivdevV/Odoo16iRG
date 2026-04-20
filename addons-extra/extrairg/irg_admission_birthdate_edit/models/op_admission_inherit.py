from odoo import models, fields


class OpAdmissionInherit(models.Model):
    _inherit = "op.admission"

    # Redefine the field without `states` so it's editable regardless of `state`.
    birth_date = fields.Date(
        string="Birth Date",
        required=True,
    )
