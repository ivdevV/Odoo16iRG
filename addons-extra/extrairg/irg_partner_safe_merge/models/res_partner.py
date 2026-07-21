from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    irg_merged_into_partner_id = fields.Many2one(
        "res.partner",
        string="Merged into",
        copy=False,
        readonly=True,
        index=True,
        ondelete="restrict",
        groups="base.group_system",
        help="Master contact selected by the administrator safe-merge service.",
    )

    _sql_constraints = [
        (
            "irg_merged_partner_not_self",
            "CHECK(irg_merged_into_partner_id IS NULL OR "
            "irg_merged_into_partner_id != id)",
            "A contact cannot be merged into itself.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("irg_merged_into_partner_id") for vals in vals_list):
            self._irg_assert_marker_service()
        return super().create(vals_list)

    def write(self, vals):
        if "irg_merged_into_partner_id" in vals:
            self._irg_assert_marker_service()
        if vals.get("active") and any(self.mapped("irg_merged_into_partner_id")):
            raise ValidationError(_("A merged source contact cannot be reactivated."))
        return super().write(vals)

    def unlink(self):
        if any(self.mapped("irg_merged_into_partner_id")):
            raise ValidationError(_("A merged source contact cannot be deleted."))
        return super().unlink()

    def _irg_assert_marker_service(self):
        if not self.env.su or not self.env.context.get("_irg_safe_merge_service"):
            raise AccessError(
                _("The merge marker can only be changed by the safe-merge service.")
            )

    @api.constrains("irg_merged_into_partner_id")
    def _check_irg_merged_chain(self):
        for partner in self:
            seen = {partner.id}
            current = partner.irg_merged_into_partner_id
            while current:
                if current.id in seen:
                    raise ValidationError(_("A contact merge cycle is not allowed."))
                seen.add(current.id)
                current = current.irg_merged_into_partner_id

    def action_irg_safe_merge(self):
        self.env["irg.partner.safe.merge.wizard"]._assert_admin()
        wizard = self.env["irg.partner.safe.merge.wizard"].create_from_selection(self.ids)
        return {
            "type": "ir.actions.act_window",
            "name": _("Safe merge"),
            "res_model": "irg.partner.safe.merge.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }
