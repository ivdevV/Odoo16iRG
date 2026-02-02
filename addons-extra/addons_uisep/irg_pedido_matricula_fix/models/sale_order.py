# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.product_id.formation_type', 'order_line.product_id.name', 'order_line.product_id.categ_id')
    def _compute_is_official(self):
        """
        Extiende el cálculo de is_official para considerar también
        si el nombre del producto o la categoría contienen "oficial".
        
        is_official será True si:
        - Algún producto tiene formation_type == 'officialdom' (comportamiento original)
        - O algún producto contiene "oficial" en el nombre (case insensitive)
        - O algún producto tiene una categoría que contiene "oficial" (case insensitive)
        """
        for order in self:
            # Verificar si algún producto tiene formation_type == 'officialdom'
            has_officialdom_type = any(
                line.product_id.formation_type == 'officialdom' 
                for line in order.order_line 
                if line.product_id
            )
            
            # Verificar si algún producto contiene "oficial" en el nombre (case insensitive)
            has_oficial_in_name = any(
                line.product_id.name and 'oficial' in line.product_id.name.lower() 
                for line in order.order_line 
                if line.product_id
            )
            
            # Verificar si algún producto tiene categoría que contiene "oficial" (case insensitive)
            has_oficial_in_category = any(
                line.product_id.categ_id and line.product_id.categ_id.name and 
                'oficial' in line.product_id.categ_id.name.lower() 
                for line in order.order_line 
                if line.product_id
            )
            
            order.is_official = has_officialdom_type or has_oficial_in_name or has_oficial_in_category
            
            # Log para debugging
            if order.is_official:
                _logger.info(
                    "Pedido %s marcado como oficial. "
                    "Por formation_type: %s, Por nombre: %s, Por categoría: %s",
                    order.name, has_officialdom_type, has_oficial_in_name, has_oficial_in_category
                )
