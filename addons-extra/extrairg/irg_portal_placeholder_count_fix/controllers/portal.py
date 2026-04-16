# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalPlaceholderCountFix(CustomerPortal):
    """Garantiza valores por defecto para badges de contador del portal."""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if isinstance(counters, (list, tuple, set)):
            for placeholder in counters:
                if values.get(placeholder) is None:
                    values[placeholder] = 0
        placeholder_keys = [
            'documents_quantity',
            'documents_count',
            'quotation_count',
            'order_count',
        ]
        for placeholder in placeholder_keys:
            if values.get(placeholder) is None:
                values[placeholder] = 0
        return values
