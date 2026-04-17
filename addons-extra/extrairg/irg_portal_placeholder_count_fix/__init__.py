# -*- coding: utf-8 -*-
from odoo.addons.portal.controllers.portal import CustomerPortal

# Guardar el método original ANTES de reemplazarlo
_original_prepare_home_portal_values = CustomerPortal._prepare_home_portal_values

# Crear un wrapper que NO causa recursión infinita
def _patched_prepare_home_portal_values(self, counters):
    """Garantiza valores por defecto para badges de contador del portal."""
    # Llamar al método original directamente (sin super())
    values = _original_prepare_home_portal_values(self, counters)
    
    # Rellenar los valores por defecto que falten
    if isinstance(counters, (list, tuple, set)):
        for placeholder in counters:
            if values.get(placeholder) is None:
                values[placeholder] = 0
    
    # Asegurar que estos placeholders siempre existan
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

# Reemplazar el método de la clase original
CustomerPortal._prepare_home_portal_values = _patched_prepare_home_portal_values
