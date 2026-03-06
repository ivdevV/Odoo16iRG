from odoo import SUPERUSER_ID, api


def _build_zero_karma_vals(Forum):
    """Set every forum karma-related field to 0."""
    return {
        field_name: 0
        for field_name, field in Forum._fields.items()
        if field_name.startswith("karma_") and getattr(field, "type", None) in ("integer", "float", "monetary")
    }


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Forum = env["forum.forum"].sudo()
    zero_vals = _build_zero_karma_vals(Forum)
    if zero_vals:
        Forum.search([]).write(zero_vals)
