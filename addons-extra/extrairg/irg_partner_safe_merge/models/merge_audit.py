from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class IrgPartnerSafeMergeAudit(models.Model):
    _name = "irg.partner.safe.merge.audit"
    _description = "Partner Safe Merge Audit"
    _order = "merged_at desc, id desc"

    master_partner_id = fields.Many2one(
        "res.partner", required=True, readonly=True, ondelete="restrict", index=True
    )
    origin_partner_id = fields.Many2one(
        "res.partner", required=True, readonly=True, ondelete="restrict", index=True
    )
    actor_id = fields.Many2one(
        "res.users", required=True, readonly=True, ondelete="restrict"
    )
    merged_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now)
    preview_hash = fields.Char(required=True, readonly=True, index=True)
    recommendation_reason = fields.Text(readonly=True)
    decisions_json = fields.Text(readonly=True, default="{}")
    inventory_json = fields.Text(readonly=True, default="{}")
    actions_json = fields.Text(readonly=True, default="{}")
    before_snapshot_json = fields.Text(readonly=True, required=True, default="{}")
    after_snapshot_json = fields.Text(readonly=True, required=True, default="{}")

    _sql_constraints = [
        (
            "irg_safe_merge_origin_unique",
            "unique(origin_partner_id)",
            "A source contact can only be merged once.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        # Only the safe-merge service may create immutable audit rows.
        if not self.env.su or not self.env.context.get("_irg_safe_merge_service"):
            raise AccessError(_("Only the safe-merge service can create merge audits."))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_("Safe-merge audits are immutable."))

    def unlink(self):
        raise AccessError(_("Safe-merge audits are immutable."))
