from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging
import traceback
_logger = logging.getLogger(__name__)

class WebsiteSaleExtends(WebsiteSale):

    def _get_or_prepare_signature_link(self, order):
        order = order.sudo()
        if not order:
            return False

        if not order.sign_id:
            order.send_automated_action()
        elif hasattr(order.sign_id, 'create_link_sign'):
            order.sign_id.create_link_sign()

        sign_template = order.sign_id
        return sign_template and sign_template.share_link_website or False

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

        except Exception as e:
            _logger.error("Error preparando firma en shop_payment: %s\n%s", e, traceback.format_exc())
        return res

    
    @http.route('/signature_status', type='json', auth='public', website=True)
    def signature_status(self, order_id):
        try:
            order = request.env['sale.order'].sudo().browse(int(order_id))
            sign_link = self._get_or_prepare_signature_link(order)
            if order and order.sign_id:
                signed = request.env['sign.request'].sudo().search_count([
                    ('template_id', '=', order.sign_id.id),
                    ('state', '=', 'signed')
                ]) > 0
                return {'signed': signed, 'sign_link': sign_link}
            return {'signed': False, 'sign_link': False}
        except Exception as e:
            _logger.error("Error en signature_status para order %s: %s\n%s", order_id, e, traceback.format_exc())
            return {'signed': False, 'sign_link': False, 'error': str(e)}

    @http.route('/signature_prepare', type='json', auth='public', website=True)
    def signature_prepare(self, order_id):
        try:
            order = request.env['sale.order'].sudo().browse(int(order_id))
            sign_link = self._get_or_prepare_signature_link(order)
            return {
                'sign_link': sign_link,
                'has_sign_template': bool(order and order.sign_id),
                'error': False,
            }
        except Exception as e:
            _logger.error("Error en signature_prepare para order %s: %s\n%s", order_id, e, traceback.format_exc())
            return {
                'sign_link': False,
                'has_sign_template': False,
                'error': str(e),
            }
