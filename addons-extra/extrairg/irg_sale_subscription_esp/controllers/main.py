# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from odoo.addons.isep_website_sale_custom.controllers.main import CustomWebsiteSale

_logger = logging.getLogger(__name__)


class IrgWebsiteSale(CustomWebsiteSale):
    """
    Hereda de CustomWebsiteSale (isep_website_sale_custom) para estar al FINAL
    de la cadena MRO de controllers. Si heredamos de WebsiteSale directamente,
    se crea una rama paralela y Odoo elige la de isep.
    """

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def confirm_order(self, **post):
        """
        Sobreescribe confirm_order para SIEMPRE ejecutar _auto_scheduled_order
        sin la restricción de subscription_schedule del módulo antiguo.
        Ejecutamos _auto_scheduled_order ANTES de llamar a super() para que la
        página renderizada por super() incluya cualquier línea de financiación
        añadida por nuestra lógica (evita que se cree la línea *después* de renderizar).
        """
        _logger.info("IRG controller confirm_order: ENTERING")
        # Ejecutar la lógica de scheduling antes de renderizar la página
        try:
            order = request.website.sale_get_order()
            if order:
                if order.subscription_schedule:
                    _logger.info("IRG confirm_order: order %s already has subscription_schedule - forcing recalculation", order.name)
                order.sudo()._auto_scheduled_order()
        except Exception as e:
            _logger.exception("IRG confirm_order pre-super _auto_scheduled_order failed: %s", e)

        # Llamar al flujo original (que ahora encontrará la orden ya actualizada)
        res = super(IrgWebsiteSale, self).confirm_order(**post)
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        """
        Sobreescribe address. Ejecutamos _auto_scheduled_order ANTES de llamar a
        super() para asegurar que la página devuelta incluye la línea de financiación
        si procede. Capturamos errores para debugging.
        """
        _logger.info("IRG controller address: ENTERING")
        # Ejecutar scheduling antes de renderizar la página
        try:
            order = request.website.sale_get_order()
            if order:
                if order.subscription_schedule:
                    _logger.info("IRG address: order %s already has subscription_schedule - forcing recalculation", order.name)
                order.sudo()._auto_scheduled_order()
        except Exception as e:
            _logger.exception("IRG address pre-super _auto_scheduled_order failed: %s", e)

        res = super(IrgWebsiteSale, self).address(**kw)
        return res

    @http.route(['/shop/extra_info'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def extra_info(self, **post):
        """
        Sobreescribe extra_info para ejecutar _auto_scheduled_order antes de renderizar
        el resumen y mantener las lineas de financiacion y matricula.
        """
        _logger.info("IRG controller extra_info: ENTERING")
        try:
            order = request.website.sale_get_order()
            if order:
                if order.subscription_schedule:
                    _logger.info("IRG extra_info: order %s already has subscription_schedule - forcing recalculation", order.name)
                order.sudo()._auto_scheduled_order()
        except Exception as e:
            _logger.exception("IRG extra_info pre-super _auto_scheduled_order failed: %s", e)

        res = super(IrgWebsiteSale, self).extra_info(**post)
        return res
