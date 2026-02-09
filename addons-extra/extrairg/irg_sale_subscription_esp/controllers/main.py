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
        # No llamamos _auto_scheduled_order aquí porque super() ya lo hace
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        """
        Sobreescribe address. super() -> CustomWebsiteSale.address ya llama
        _auto_scheduled_order internamente, no necesitamos llamarlo otra vez.
        """
        _logger.info("IRG controller address: ENTERING")
        res = super(IrgWebsiteSale, self).address(**kw)
        # No llamamos _auto_scheduled_order aquí porque super() ya lo hace
        return res
