from odoo import api, models


def _build_zero_karma_vals(Forum):
    return {
        field_name: 0
        for field_name, field in Forum._fields.items()
        if field_name.startswith("karma_") and getattr(field, "type", None) in ("integer", "float", "monetary")
    }


class ForumForum(models.Model):
    _inherit = "forum.forum"

    @api.model_create_multi
    def create(self, vals_list):
        zero_vals = _build_zero_karma_vals(self)
        if zero_vals:
            vals_list = [{**vals, **zero_vals} for vals in vals_list]
        return super().create(vals_list)

    def write(self, vals):
        zero_vals = _build_zero_karma_vals(self)
        if zero_vals and any(field_name in vals for field_name in zero_vals):
            vals = {**vals, **zero_vals}
        return super().write(vals)
