from odoo import tools


def uninstall_hook(cr, registry):
    tools.drop_index(
        cr,
        'irg_scp_active_partner_channel_batch_uniq',
        'slide_channel_partner',
    )
