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
        super() -> CustomWebsiteSale.confirm_order (que llama al base y opcionalmente
        ejecuta _auto_scheduled_order con condición bloqueante).
        Nosotros SIEMPRE lo ejecutamos después para asegurar la financiación.
        """
        _logger.info("IRG controller confirm_order: ENTERING")
        res = super(IrgWebsiteSale, self).confirm_order(**post)
        try:
            order = request.website.sale_get_order()
            _logger.info("IRG controller confirm_order: order=%s, partner=%s",
                         order.name if order else 'NONE',
                         order.partner_id.id if order else 'N/A')
            if order and order.partner_id.id != 4:
                _logger.info("IRG controller confirm_order: Calling _auto_scheduled_order for %s", order.name)
                order.sudo()._auto_scheduled_order()
            else:
                _logger.info("IRG controller confirm_order: No order or public user, skipping")
        except Exception as e:
            _logger.error("IRG controller confirm_order: Error: %s", str(e), exc_info=True)
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        """
        Sobreescribe address para ejecutar _auto_scheduled_order al completar dirección.
        """
        _logger.info("IRG controller address: ENTERING")
        res = super(IrgWebsiteSale, self).address(**kw)
        try:
            order = request.website.sale_get_order()
            if order and order.partner_id.id != 4:
                _logger.info("IRG controller address: Calling _auto_scheduled_order for %s", order.name)
                order.sudo()._auto_scheduled_order()
        except Exception as e:
            _logger.error("IRG controller address: Error: %s", str(e), exc_info=True)
        return res
