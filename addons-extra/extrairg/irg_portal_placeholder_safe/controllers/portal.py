# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalPlaceholderSafe(CustomerPortal):
    """Extiende `portal.CustomerPortal` para asegurar valores por defecto
    para placeholders que el JS del portal puede actualizar.
    """

    def _prepare_home_portal_values(self, counters):
        values = super(CustomerPortalPlaceholderSafe, self)._prepare_home_portal_values(counters)

        # Si `counters` es iterable, asegurar que las keys solicitadas existan
        if isinstance(counters, (list, tuple, set)):
            for placeholder in counters:
                if values.get(placeholder) is None:
                    values[placeholder] = 0

        # Asegurar claves conocidas que el portal puede actualizar
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
