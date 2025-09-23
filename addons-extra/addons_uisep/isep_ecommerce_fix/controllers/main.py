from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging
_logger = logging.getLogger(__name__)

class WebsiteSaleExtends(WebsiteSale):

    @http.route('/shop/payment', type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        res = super().shop_payment(**post)
        try:
            order = request.website.sale_get_order()
            if not order:
                return res
            
            order_line = order.order_line.filtered(
                lambda x: x.product_template_id.is_academic_program and x.product_template_id.recurring_invoice
            )

            has_tesis = any(order_line.mapped('product_template_id.is_tesis'))

            if order_line and not has_tesis and not order.website_send_mail and order.is_from_website_origin and not order.sign_id:
                order.sudo().send_automated_action()
                order.sudo().write({'website_send_mail': True})

        except:
            pass
        return res

    
    @http.route('/signature_status', type='json', auth='public', website=True)
    def signature_status(self, order_id):
        order = request.env['sale.order'].sudo().browse(int(order_id))
        if order and order.sign_id:
            signed = request.env['sign.request'].sudo().search_count([
                ('template_id', '=', order.sign_id.id),
                ('state', '=', 'signed')
            ]) > 0
            return {'signed': signed}
        return {'signed': False}
