# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def search_user_portal(self):
        # Override para evitar que isep_openeducat_sale machaque el partner_id 
        # con el partner del pedido (titular) si ya hemos asignado uno diferente (el alumno).
        # isep_openeducat_sale.models.op_admission.search_user_portal comprueba si falta student_id
        # y si falta, resetea el partner_id al sale_id.partner_id.
        
        # Si nosotros ya establecimos un partner_id que es diferente del titular del pedido,
        # asumimos que es el Alumno correcto y bloqueamos esa lógica.
        if self.partner_id and self.sale_id and self.partner_id != self.sale_id.partner_id:
            _logger.info(f"ISEP_DEBUG: OpAdmission.search_user_portal - PRESERVANDO ALUMNO: {self.partner_id.name} (ID: {self.partner_id.id}) en lugar de Titular: {self.sale_id.partner_id.name}")
            return
        
        return super(OpAdmission, self).search_user_portal()
