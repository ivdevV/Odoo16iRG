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

    def _irg_call_super_skip_custom_autoschedule(self, super_call):
        key = 'irg_skip_custom_autoschedule'
        previous = request.session.get(key)
        request.session[key] = True
        try:
            return super_call()
        finally:
            if previous is None:
                request.session.pop(key, None)
            else:
                request.session[key] = previous

    def _irg_recalculate_once(self, order, route_name):
        """Run expensive scheduling logic at most once per HTTP request."""
        if not order:
            return

        marker = '_irg_auto_scheduled_order_done'
        if getattr(request, marker, False):
            _logger.debug("IRG %s: skipping duplicate _auto_scheduled_order for order %s", route_name, order.name)
            return

        # Defer heavy scheduling during intermediate checkout screens.
        # This keeps address -> extra_info navigation responsive.
        if request.httprequest.path in ('/shop/address', '/shop/extra_info'):
            return

        if order.subscription_schedule:
            _logger.info("IRG %s: order %s already has subscription_schedule - forcing recalculation", route_name, order.name)
        order.sudo()._auto_scheduled_order()
        setattr(request, marker, True)

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
            self._irg_recalculate_once(order, 'confirm_order')
        except Exception as e:
            _logger.exception("IRG confirm_order pre-super _auto_scheduled_order failed: %s", e)

        # Llamar al flujo original (que ahora encontrará la orden ya actualizada)
        res = self._irg_call_super_skip_custom_autoschedule(
            lambda: super(IrgWebsiteSale, self).confirm_order(**post)
        )
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
            self._irg_recalculate_once(order, 'address')
        except Exception as e:
            _logger.exception("IRG address pre-super _auto_scheduled_order failed: %s", e)

        res = self._irg_call_super_skip_custom_autoschedule(
            lambda: super(IrgWebsiteSale, self).address(**kw)
        )
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
            self._irg_recalculate_once(order, 'extra_info')
        except Exception as e:
            _logger.exception("IRG extra_info pre-super _auto_scheduled_order failed: %s", e)

        res = super(IrgWebsiteSale, self).extra_info(**post)
        return res
