# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class IrgWebsiteSale(WebsiteSale):

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        """
        Sobrescribe la actualización del carrito para forzar el recálculo de financiación
        cada vez que se modifica el carrito.
        """
        res = super(IrgWebsiteSale, self).cart_update_json(product_id, line_id, add_qty, set_qty, display, **kw)
        
        order = request.website.sale_get_order()
        if order:
            # Forzamos el recálculo de la financiación/agenda
            # Ignoramos la restricción de subscription_schedule para asegurar que se actualice
            # si cambian las cantidades o productos.
            order.sudo()._auto_scheduled_order()
            
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        """
        Asegura que al pasar por la dirección (paso previo al pago) se recalculen los gastos.
        """
        res = super(IrgWebsiteSale, self).address(**kw)
        order = request.website.sale_get_order()
        if order and order.partner_id.id != 4: # Ignorar usuario publico generico si es necesario
             # Forzamos actualización incluso si ya tiene cronograma
             order.sudo()._auto_scheduled_order()
        return res
