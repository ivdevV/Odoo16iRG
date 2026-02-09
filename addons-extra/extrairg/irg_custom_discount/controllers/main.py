# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class IrgDiscountController(WebsiteSale):

    @http.route(['/shop/pricelist'], type='http', auth="public", website=True, sitemap=False)
    def pricelist(self, promo=None, **post):
        """
        Intercepta la aplicación de códigos de descuento.
        Primero comprueba si es un código IRG personalizado.
        Si no lo es, deja pasar al flujo estándar (loyalty/pricelist).
        """
        if promo:
            order = request.website.sale_get_order()
            if order:
                _logger.info("IRG Discount Controller: Checking code '%s' for order %s", promo, order.name)
                success, message = order.sudo()._irg_try_apply_discount_code(promo)

                if success:
                    # Código IRG válido y aplicado
                    _logger.info("IRG Discount Controller: Code applied successfully")
                    return request.redirect('/shop/cart')

                if message:
                    # Es un código IRG pero con error (expirado, límite, etc.)
                    # Mostrar error y no pasar al loyalty
                    _logger.info("IRG Discount Controller: IRG code error: %s", message)
                    request.session['irg_discount_error'] = message
                    return request.redirect('/shop/cart')

                # message vacío = no es un código IRG, dejamos pasar al flujo estándar
                _logger.info("IRG Discount Controller: Not an IRG code, passing to standard flow")

        return super(IrgDiscountController, self).pricelist(promo=promo, **post)
