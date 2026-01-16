# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def submit_form(self):
        """
        Override de submit_form para preservar el partner_id correcto (el alumno)
        cuando es diferente del titular del pedido.
        
        El problema: isep_elearning_custom.models.op_admission.submit_form() 
        sobrescribe partner_id con sale_line_id.order_partner_id (el titular).
        
        Solución: Guardar el partner_id correcto antes de llamar a super(),
        y restaurarlo después si fue cambiado incorrectamente.
        """
        # Guardar el partner_id actual ANTES de llamar a super()
        original_partner_id = self.partner_id
        
        # Determinar si debemos preservar el partner_id
        should_preserve = False
        if self.sale_id:
            student_from_order = self.sale_id.student_id
            titular_from_order = self.sale_id.partner_id
            
            if student_from_order and student_from_order != titular_from_order:
                should_preserve = True
                _logger.warning("=" * 60)
                _logger.warning("ISEP_ADMISSION_FROM_STUDENT: submit_form EJECUTADO")
                _logger.warning(f"Admisión: {self.name} (ID: {self.id})")
                _logger.warning(f"partner_id ANTES de super(): {original_partner_id.name if original_partner_id else 'VACIO'}")
                _logger.warning(f"sale_id.student_id (Alumno): {student_from_order.name}")
                _logger.warning(f"sale_id.partner_id (Titular): {titular_from_order.name}")
                _logger.warning("Alumno != Titular -> PRESERVAREMOS el partner_id")
        
        # Llamar al método original
        res = super(OpAdmission, self).submit_form()
        
        # Restaurar el partner_id si fue cambiado incorrectamente
        if should_preserve and self.partner_id != original_partner_id:
            _logger.warning(f"partner_id fue cambiado a: {self.partner_id.name if self.partner_id else 'VACIO'}")
            _logger.warning(f"RESTAURANDO partner_id a: {original_partner_id.name}")
            self.partner_id = original_partner_id
            _logger.warning("=" * 60)
        elif should_preserve:
            _logger.warning(f"partner_id NO fue cambiado, sigue siendo: {self.partner_id.name}")
            _logger.warning("=" * 60)
        
        return res

    def search_user_portal(self):
        """
        Override para evitar que isep_openeducat_sale machaque el partner_id 
        con el partner del pedido (titular) si ya hemos asignado uno diferente (el alumno).
        """
        if self.sale_id:
            student_from_order = self.sale_id.student_id
            titular_from_order = self.sale_id.partner_id
            
            # Si hay un alumno diferente al titular, PRESERVAR el partner_id actual
            if student_from_order and student_from_order != titular_from_order:
                _logger.info("search_user_portal: Bloqueando cambio - Alumno != Titular")
                return
        
        return super(OpAdmission, self).search_user_portal()
