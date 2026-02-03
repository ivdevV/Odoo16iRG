# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalFix(CustomerPortal):
    """
    Este controlador asegura que el contador 'documents_quantity' 
    (usado por isep_record_request) también esté disponible para evitar
    el error de JavaScript cuando el portal intenta actualizar el contador.
    
    El error original:
    "Cannot set properties of null (setting 'textContent')"
    ocurre porque el JS busca un elemento con data-placeholder_count='documents_quantity'
    pero el valor no está siendo devuelto correctamente.
    """

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        
        # Asegurar que documents_quantity siempre tenga un valor
        # para evitar el error de JS cuando el elemento existe pero el valor es null
        if 'documents_quantity' in counters:
            if 'documents_quantity' not in values or values.get('documents_quantity') is None:
                # Usar el mismo valor que documents_count si existe
                values['documents_quantity'] = values.get('documents_count', 0)
        
        return values
