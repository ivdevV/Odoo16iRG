def post_init_hook(cr, registry):
    """
    Post-install hook to sync existing product_template_id data to product_template_ids
    """
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Sync existing data
    env['op.course']._sync_product_fields()
