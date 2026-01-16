# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def search_user_portal(self):
        """
        Override para evitar que isep_openeducat_sale machaque el partner_id 
        con el partner del pedido (titular) si ya hemos asignado uno diferente (el alumno).
        
        isep_openeducat_sale.models.op_admission.search_user_portal comprueba si falta student_id
        y si falta, resetea el partner_id al sale_id.partner_id.
        
        Si nosotros ya establecimos un partner_id que es diferente del titular del pedido,
        asumimos que es el Alumno correcto y bloqueamos esa lógica.
        """
        _logger.warning("=" * 60)
        _logger.warning("ISEP_ADMISSION_FROM_STUDENT: search_user_portal EJECUTADO")
        _logger.warning(f"Admisión: {self.name} (ID: {self.id})")
        _logger.warning(f"partner_id actual: {self.partner_id.name if self.partner_id else 'VACIO'}")
        
        if self.sale_id:
            # Obtener el alumno del pedido de venta
            student_from_order = self.sale_id.student_id
            titular_from_order = self.sale_id.partner_id
            
            _logger.warning(f"sale_id.student_id (Alumno): {student_from_order.name if student_from_order else 'VACIO'}")
            _logger.warning(f"sale_id.partner_id (Titular): {titular_from_order.name if titular_from_order else 'VACIO'}")
            
            # Si hay un alumno diferente al titular, PRESERVAR el partner_id actual de la admisión
            # (que debería ser el alumno, no el titular)
            if student_from_order and student_from_order != titular_from_order:
                _logger.warning(f"BLOQUEANDO cambio de partner - Alumno es diferente al Titular")
                _logger.warning(f"Preservando partner_id: {self.partner_id.name}")
                _logger.warning("=" * 60)
                return  # No ejecutar super(), no dejar que cambie el partner_id
        
        _logger.warning("Ejecutando super().search_user_portal()")
        _logger.warning("=" * 60)
        return super(OpAdmission, self).search_user_portal()
