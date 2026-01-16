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

            # CORRECCIÓN ADICIONAL: Verificar y restaurar student_id
            # Si isep_elearning_custom cambió el partner, también pudo haber asignado el student_id del titular
            if self.student_id and self.student_id.partner_id != original_partner_id:
                _logger.warning(f"student_id incorrecto detectado: {self.student_id.name} (Partner vinculado: {self.student_id.partner_id.name})")
                
                # Buscar si ya existe un estudiante para el partner correcto
                correct_student = self.env['op.student'].search([('partner_id', '=', original_partner_id.id)], limit=1)
                
                if not correct_student:
                    _logger.warning(f"Creando nuevo op.student para el partner correcto: {original_partner_id.name}")
                    
                    # Intentar obtener usuario asociado al partner si existe
                    user_for_student = False
                    if original_partner_id.user_ids:
                        user_for_student = original_partner_id.user_ids[0]
                    
                    details = {
                        'title': self.title and self.title.id or False,
                        'first_name': self.first_name,
                        'middle_name': self.middle_name,
                        'last_name': self.last_name,
                        'birth_date': self.birth_date,
                        'gender': self.gender,
                        # Usamos self.image como en isep_elearning_custom, asumiendo que existe en el modelo
                        'image_1920': self.image or False,
                        'user_id': user_for_student.id if user_for_student else False,
                        'company_id': self.company_id.id,
                        'partner_id': original_partner_id.id,
                    }
                    correct_student = self.env['op.student'].create(details)
                
                _logger.warning(f"RESTAURANDO student_id a: {correct_student.name} (ID: {correct_student.id})")
                self.student_id = correct_student.id

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
        _logger.warning(f"ISEP_ADMISSION_FROM_STUDENT: search_user_portal INVOCADO para id={self.id}")
        if self.sale_id:
            _logger.warning("ISEP_ADMISSION_FROM_STUDENT: search_user_portal con sale_id")
            student_from_order = self.sale_id.student_id
            titular_from_order = self.sale_id.partner_id
            
            if self.partner_id:
                 _logger.warning(f"  > Partner actual en admisión: {self.partner_id.name} (ID: {self.partner_id.id})")
            
            # Si hay un alumno diferente al titular, PRESERVAR el partner_id actual
            if student_from_order and student_from_order != titular_from_order:
                _logger.warning(f"  > Detectado Alumno ({student_from_order.name}) != Titular ({titular_from_order.name})")
                _logger.warning("  > BLOQUEANDO search_user_portal original para evitar sobrescritura.")
                return
        
        return super(OpAdmission, self).search_user_portal()
